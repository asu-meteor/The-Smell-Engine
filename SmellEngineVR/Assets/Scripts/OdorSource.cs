using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class OdorSource : MonoBehaviour
{
    public List<OdorantMolecule> odorantMolecules;

    public List<double> GetListConcentrations() {
        List<double> concentrations = new List<double>();
        foreach (OdorantMolecule om in odorantMolecules) concentrations.Add(om.concentration);        
        return concentrations;
    }
}

[System.Serializable]
public class OdorantMolecule {
    public int OM_ID;
    public double concentration;
    public double spreadDistance;
}