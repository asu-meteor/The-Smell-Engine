using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.IO;
using System.Linq;

public class OdorMixer : MonoBehaviour {
    [Header("Unity Components")]
    public SocketClient sc;
    public GameObject player;
    public Plotter plotter;
    public OdorMixVector odorMixVector;
    [Header("Component Lists")] 
    public List<OdorSource> odorSources;
    public int[] Dilutions;    
    [SerializeField]
    public List<int> PubChemIDs;
    protected Dictionary<int, double> OdorMix;

    [Header("Flags")]
    public int eventsPerSecond;
    public bool debug_mode;    
    public bool collider_based;


    private double[] oldConcentrationVector;
    #region private_values
    private double[] networkValues;    
    private bool triggered_enter;
    private bool triggered_exit;
    #endregion

    public class OdorMixVector {
        public double[] concentrationVector;
        public void Initialize(int numConc) {
            concentrationVector = new double[numConc];
            for (int i = 0; i < concentrationVector.Length; i++) concentrationVector[i] = -30.0f;            
        }

        public string PrintString() {
            string output_result = "";
            for(int i=0; i<concentrationVector.Length; i++) output_result += "\ni: " + i + ", conc_vect_val: " + concentrationVector[i];            
            return output_result;
        }

        public void CalculateLogValues() {
            for (int i = 0; i < concentrationVector.Length; i++) {
                if (concentrationVector[i] == 0)    concentrationVector[i] = -30.0f;
                else                                concentrationVector[i] = Mathf.Log10((float)concentrationVector[i]);

                //if (float.IsNaN((float)concentrationVector[i])) concentrationVector[i] = -30.0f;
                //Debug.Log($"Log value Conc  {i}, {concentrationVector[i]}");
            }
        }
    }

    private void InitializeSystemProperties() {
        if (odorSources.Count == 0) odorSources = GameObject.FindObjectsOfType<OdorSource>().ToList();
        PubChemIDs = new List<int>();
        OdorMix = new Dictionary<int, double>();
        foreach (OdorSource m_odorSource in odorSources) {
            foreach (OdorantMolecule om in m_odorSource.odorantMolecules) {
                if (!PubChemIDs.Contains(om.OM_ID)) {   // if PubChemID not stored prev, store now.
                    PubChemIDs.Add(om.OM_ID);
                    OdorMix.Add(om.OM_ID, 0.0f);
                }
            }
        }
    }

    void Awake() {
        oldConcentrationVector = new double[odorSources.Count]; 
       
        triggered_enter = triggered_exit = false;
        odorMixVector = new OdorMixVector();

        InitializeSystemProperties();
        odorMixVector.Initialize(PubChemIDs.Count);
        Debug.Log(odorMixVector.PrintString());

        if (eventsPerSecond == 0)           eventsPerSecond = 1;                
    }

    private void Start() {
        // Transmit the PubID's to the Olfactometer.
        if (!debug_mode) {
            sc.TransmitNumberOfOdorants(new int[1] { PubChemIDs.Count });  // Transmit # of odorants to init            
            sc.TransmitPubChemIDs(PubChemIDs);              // Transmit Odor IDs
            sc.TransmitDilutions(Dilutions);
            networkValues = new double[odorMixVector.concentrationVector.Length];
            if (collider_based) TransmitValues();
        }
        if (collider_based) {
            FixedOlfactionTrigger.OnEnteredSpace += FixedConcentrationTransmit;
            FixedOlfactionTrigger.OnExitedSpace += AirTransmit;
        }
        // If ! collider, calculate concentrations once a second
        if (!collider_based)    InvokeRepeating("CalculateConcentrations", 5.0f, 1.0f / eventsPerSecond);
        if (collider_based)     InvokeRepeating("TransmitValues", 5.0f, 1.0f / eventsPerSecond);
    }


    /// <summary>
    /// Return vector distance of user from smell object/game object.
    /// </summary>    
    /// <returns></returns>
    public float CalculateUserDistance(GameObject distanceFrom) {
        //Debug.Log($"User Dist:\t {Vector3.Distance(player.transform.position, distanceFrom.transform.position)}");
        return Mathf.Abs(Vector3.Distance(player.transform.position, distanceFrom.transform.position));
    }
    

    /// <summary>
    /// Delegate method for collision based odor diffusion
    /// </summary>
    /// <param name="odor">Distinctive odor object for reading odor mixture feature vector</param>
    public void FixedConcentrationTransmit(OdorSource odorSrc) {
        if (!collider_based) return;
        odorMixVector.Initialize(PubChemIDs.Count);
        Debug.Log(odorMixVector.PrintString());
        double[] odorSrcConcVector = odorSrc.GetListConcentrations().ToArray();
        System.Array.Copy(odorSrcConcVector,
                            odorMixVector.concentrationVector,
                            odorSrcConcVector.Length);
        odorMixVector.CalculateLogValues();
        //Debug.Log($"Entered odor space:\t{odor.gameObject.name}, conc now:\t{odorMixVector.PrintString()}");                
        triggered_enter = true;
        triggered_exit = false;
    }

    public void AirTransmit(OdorSource odor) {
        if (!collider_based) return;
        triggered_enter = false;
        triggered_exit = true;        
    }


    /// <summary>
    /// if user barely moves, don't transmit odorants, let duty cycle repeat
    /// Calculate dot product between previous odor feature vector and current
    /// to adjust resolution of values transmitted
    /// </summary>
    /// <returns>Floating point value for comparing threshold</returns>
    private float DistSquared(double[] x, double[] y) {
        float dot = 0;
        if (x.Length != y.Length)           return 100;
        for (int i = 0; i < x.Length; i++) {
            //Debug.Log($"x {x[i]}, float x {(float)x[i]},  y {y[i]} float y {(float)y[i]}");
            //Debug.Log($"Diff {(float)x[i] - (float)y[i]}");
            dot += Mathf.Pow(((float)x[i] - (float)y[i]), 2);
        }
        //Debug.Log($"Dot product {dot}");
        return dot;
    }

    protected void ResetOdorMixValues()
    {
        foreach (OdorSource mOdorSource in odorSources)
        {   // Plug into equation the sigma & concentrations for olfactory obj

            foreach (OdorantMolecule om in mOdorSource.odorantMolecules)
            {
                if (OdorMix.ContainsKey(om.OM_ID))
                {
                    OdorMix[om.OM_ID] = 0.0f;
                }
            }
        }
    }

    public void CalculateConcentrations() {

        odorMixVector.Initialize(PubChemIDs.Count);
        ResetOdorMixValues();
        Debug.Log(odorMixVector.PrintString());
        //for (int i = 0; i < odorMixVector.concentrationVector.Length; i++) odorMixVector.concentrationVector[i] = 0;        
        foreach (OdorSource mOdorSource in odorSources) {   // Plug into equation the sigma & concentrations for olfactory obj

            foreach (OdorantMolecule om in mOdorSource.odorantMolecules) {
                if (OdorMix.ContainsKey(om.OM_ID)) {
                    OdorMix[om.OM_ID] += om.concentration * Mathf.Exp((-1.0f * Mathf.Pow(CalculateUserDistance(mOdorSource.gameObject) / (float) om.spreadDistance, 2.0f)));                    
                }
            }
                //    odorMixVector.concentrationVector[i] +=
                //        smell.concentrations.concentrationVector[i] * Mathf.Exp((-1.0f * Mathf.Pow(CalculateUserDistance(smell.gameObject) / smell.sigmas.sigmaVector[i], 2.0f)));                
                //    //Debug.Log($"CALC Conc ID:{PubChemIDs[i]}, {i}, Value:{odorMixVector.concentrationVector[i]}");                
        }
        int counter = 0;
        foreach (KeyValuePair<int, double> odorMix in OdorMix) {
            //Debug.Log($"Assigning {odorMix.Value} to odor Mix Vector at index {counter}");
            odorMixVector.concentrationVector[counter] = odorMix.Value;            
            counter++;
        }
        odorMixVector.CalculateLogValues();        
        if (!debug_mode) {  // Transmit data
            float user_dist_check_val = DistSquared(oldConcentrationVector, odorMixVector.concentrationVector);            
            if (!float.IsNaN(user_dist_check_val) && user_dist_check_val > 1e-12) {                
                oldConcentrationVector = odorMixVector.concentrationVector;
                Debug.Log("Transmitting value");
                if (!debug_mode)    TransmitValues();
            } else if (float.IsNaN(user_dist_check_val)) {  // in case of overflow
                Debug.Log("NaN");
                for (int i = 0; i < odorMixVector.concentrationVector.Length; i++) odorMixVector.concentrationVector[i] = -30.0f;                
                oldConcentrationVector = odorMixVector.concentrationVector;
            }
        }
    }

    /// <summary>
    /// Convert float to decimal to double bc
    /// double is binary representation of decimal value.
    /// </summary>
    /// <param name="values">Odor Feature Vector as logairthmic values (conv to double for encoding/decoding of sockets</param>
    public void TransmitValues() {
        double[] values = odorMixVector.concentrationVector;
        if (collider_based) {
            for (int i = 0; i < values.Length; i++) {
                //Debug.Log($"Trigger based value before double conversion:{values[i]}");
                if (triggered_exit) values[i] = -30.0f;    
                //if (float.IsNaN(values[i])) values[i] = -30.0f;             //  CHECK OVERFLOW
                //double conversion = System.Convert.ToDouble(System.Convert.ToDecimal(values[i]));
                networkValues[i] = values[i] == 0 ? -30 : values[i];
                Debug.Log($"Conc ID:{PubChemIDs[i]}, Value:{networkValues[i]}");
            }
        } else {
            for (int i = 0; i < values.Length; i++) {                                     
                //double conversion = System.Convert.ToDouble(System.Convert.ToDecimal(values[i]));
                networkValues[i] = values[i] == 0 ? -30 : values[i];
                Debug.Log($"Conc ID:{PubChemIDs[i]}, Value:{networkValues[i]}");
            }
        }
        if (!debug_mode)    sc.ExecuteClient(networkValues);
    }


    public void OnDestroy() {
        sc.CloseConnection();
    }


    
}
