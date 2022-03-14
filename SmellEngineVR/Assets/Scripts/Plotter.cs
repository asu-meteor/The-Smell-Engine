using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using TMPro;

/// <summary>
/// Plot 5 different sources of data in differet colors using a line graph.
/// Retain all data recorded for session, graph data using a translated range.
/// </summary>
public class Plotter : MonoBehaviour
{
    private List<string> PubIDs;
    public List<AxisItem> DataSet { get; set; }         // Record all data instances.
    public List<AxisItem> BufferDataSet { get; set; }   // Plot transferred data in segments using this list.
    public Color[] emptyColors, colors, blackout;

    [HideInInspector]
    public Texture2D plotGraph;
    [HideInInspector]
    public int graphDimension;

    public ColorMolecule[] coloring;
    public RawImage graph;
    public GameObject tickText;
    public TextMeshProUGUI minText, maxText;
    public int XAxisTicks, YAxisTicks;
    private float minTick, maxTick;
    private int y_pixelsPerTick, x_pixelsPerTick;
    private float x_secondsPerTick = 5.0f;


    // Make this a templated object so custom defined pairs can be defined then passed.
    public struct AxisItem {
        public AxisItem(OdorMixer.OdorMixVector c,float t) {
            Concentration = c;
            Timestamp = t;
        }
        public OdorMixer.OdorMixVector Concentration { get; }
        public float Timestamp { get; }
    }

    public struct ColorMolecule {
        public Color[] colorCode;
        public ColorMolecule(Color c) {
            colorCode = new Color[2] { c, c };
        }
    }

    public void Awake() {
        DataSet = new List<AxisItem>();
        BufferDataSet = new List<AxisItem>();
        minTick = Mathf.Infinity;
        maxTick = Mathf.Infinity * -1.0f;
        graphDimension = (int)graph.rectTransform.rect.width;
        y_pixelsPerTick = graphDimension / YAxisTicks;
        x_pixelsPerTick = graphDimension / XAxisTicks;
        plotGraph = new Texture2D(graphDimension, graphDimension);
        graph.texture = plotGraph;
        blackout = new Color[2] { Color.black, Color.black };
        colors = new Color[(int)Mathf.Pow(graphDimension, 2.0f)];
        emptyColors = new Color[(int)Mathf.Pow(graphDimension, 2.0f)];
        // Populate empty array colors & assign texture.
        for (int i=0;i<emptyColors.Length;i++) {
            emptyColors[i] = Color.black;
        }
        ConfigureTicks();
        coloring = new ColorMolecule[5] { new ColorMolecule(Color.red),
                                            new ColorMolecule(Color.green),
                                            new ColorMolecule(Color.magenta),
                                            new ColorMolecule(Color.yellow),
                                            new ColorMolecule(Color.cyan)};
    }

    

    public void ConfigureTicks() {
        // Color pixels for delta y.
        for (int i = 0; i < YAxisTicks; i++) {
            // Fill in x axis.
            emptyColors[i * y_pixelsPerTick] = Color.white;
            emptyColors[i * (y_pixelsPerTick) + graphDimension] = Color.white;
            emptyColors[i * (y_pixelsPerTick) + graphDimension * 2] = Color.white;
            emptyColors[i * (y_pixelsPerTick) + graphDimension * 3] = Color.white;
            // Fill in y axis.
            emptyColors[(i * graphDimension) * y_pixelsPerTick] = Color.white;
            emptyColors[(i * graphDimension) * y_pixelsPerTick + 1] = Color.white;
            emptyColors[(i * graphDimension) * y_pixelsPerTick + 2] = Color.white;
            emptyColors[(i * graphDimension) * y_pixelsPerTick + 3] = Color.white;
        }
        emptyColors.CopyTo(colors, 0);
        plotGraph.SetPixels(colors);
        plotGraph.Apply();
    }


    public void FindMinMaxDataPoint(ref float min, ref float max) {
        foreach (AxisItem dp in BufferDataSet) {
            foreach(float element in dp.Concentration.concentrationVector) {
                if (element < min) min = element;
                if (element > max) max = element;
            }
        }
    }

    /// <summary>
    /// 1. Update buffer, remove first value & set its corresponding pixel to black.
    /// 2. Calculate new min max values.
    /// 3. Scale datapoints with respect to min/max.
    /// 4. PlotPixels.
    /// </summary>
    /// <param name="cVector"></param>
    public void AddDataPoint(OdorMixer.OdorMixVector cVector) {
        AxisItem element = new AxisItem(cVector, Time.time % 240);

        DataSet.Add(element);
        // Calculate new min max, and plot.
        BufferDataSet.Add(element);
        // Minding min/max
        float dpMin = Mathf.Infinity;
        float dpMax = Mathf.Infinity * -1.0f;
        FindMinMaxDataPoint(ref dpMin, ref dpMax);
        minTick = dpMin;
        maxTick = dpMax;
        //minTick = -30.0f;
        //maxTick = -1.0f;
        //minTick = minTick > dpMin ? dpMin : minTick;
        //maxTick = maxTick < dpMax ? dpMax : maxTick;
        minText.SetText(string.Format("Min:\t{0}", minTick));
        maxText.SetText(string.Format("Max:\t{0}", maxTick));
        //Debug.Log(string.Format("Min:\t{0}, Max:\t{1}", minTick, maxTick));
        PlotData();  // Scale Values to pixel space.
    }
    
    public void PlotData() {

        emptyColors.CopyTo(colors, 0);
        // To create oscillator effect, we subtract the plotted point per frame from number of ticks 
        // to be plotted.
        float starttime = BufferDataSet[BufferDataSet.Count - 1].Timestamp - XAxisTicks*x_secondsPerTick;
        // By checking if Timestamp>starttime we determine if data time has passed graph view.
        for (int i = BufferDataSet.Count -1; i >= 0 && BufferDataSet[i].Timestamp>starttime; --i) {            
            // To get pixel location, we take most recent point and scale how many ticks can be shown 
            // on x axis.
            float xPixel = (BufferDataSet[i].Timestamp - starttime) / x_secondsPerTick * x_pixelsPerTick;   
            // Plot all the vector values for this timestamp.
            for (int j = 0; j < BufferDataSet[i].Concentration.concentrationVector.Length; j++) {
                float yPixel = (float) BufferDataSet[i].Concentration.concentrationVector[j] - minTick;
                yPixel /= maxTick - minTick;
                yPixel *= graphDimension;
                /*Debug.Log(string.Format("X:{0} from: {1} starting time segment at:\t{2}\nY:{3} from: {4}",
                    (int)xPixel, BufferDataSet[i].Timestamp, starttime, (int)yPixel, 
                    BufferDataSet[i].Concentration.concentrationVector[j]));*/
                //Debug.Log("V1:\t" + BufferDataSet[i-1].Concentration.concentrationVector[0]);
                if (xPixel >= 1 && xPixel<249 && yPixel<249 && yPixel >=0) {
                    // Assign color by finding row (y*dimension) & column (+ xPixel).
                    colors[(int)xPixel + (int)yPixel * graphDimension] = coloring[j].colorCode[0];
                    if (BufferDataSet.Count > 1 && i > 1) {
                        float xPrior = (BufferDataSet[i - 1].Timestamp - starttime) / x_secondsPerTick * x_pixelsPerTick;
                        float yPrior = (float) BufferDataSet[i - 1].Concentration.concentrationVector[j] - minTick;
                        yPrior /= maxTick - minTick;
                        yPrior *= graphDimension;
                        float xS = (xPixel - xPrior);
                        float yS = (yPixel - yPrior);
                        float slope = (yS / xS);
                        //Debug.Log("Y s:\t" + yPixel + "Y Prior:\t" + yPrior + ", X s:\t" + xPixel + ", X prior:\t" + xPrior + ", S:\t" + slope);
                        for (int k = (int)xPrior; k < (int)xPixel; k++) {
                            int pix = (int)(slope * k - slope * xPrior + yPrior);
                            if (k >= 1 && k < 249 && pix < 249 && pix >= 0)
                                colors[k + pix * graphDimension] = coloring[j].colorCode[0];
                        }
                        /*PlotSlope(BufferDataSet[i].Timestamp, BufferDataSet[i + 1].Timestamp,
                            BufferDataSet[i].Concentration.concentrationVector[j], 
                            BufferDataSet[i + 1].Concentration.concentrationVector[j], 
                            starttime, j);*/
                    }
                }
            }
            
        }
        plotGraph.SetPixels(colors);
        plotGraph.Apply();
    }
    void PlotSlope(float xPrior, float xCurrent, float yPrior, float yCurrent, float starttime, int j) {
        xPrior = (xPrior - starttime) / x_secondsPerTick * x_pixelsPerTick;
        yPrior = yPrior - minTick;
        yPrior /= maxTick - minTick;
        yPrior *= graphDimension;
        float xS = (xCurrent - xPrior);
        float yS = (yCurrent - yPrior);
        float slope = (yS / xS);
        //Debug.Log("Y s:\t" + yPixel + "Y Prior:\t" + yPrior + ", X s:\t" + xPixel + ", X prior:\t" + xPrior + ", S:\t" + slope);
        for (int k = (int)xPrior; k < (int)xCurrent; k++) {
            int pix = (int)(slope * k - slope * xPrior + yPrior);
            if (k >= 1 && k < 249 && pix < 249 && pix >= 0)
                colors[k + pix * graphDimension] = coloring[j].colorCode[0];
        }
    }

}
