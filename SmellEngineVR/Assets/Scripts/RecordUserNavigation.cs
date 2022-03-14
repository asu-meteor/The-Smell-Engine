using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class RecordUserNavigation : MonoBehaviour {
    public UIListener uiListener;
    public string subject_name;
    public bool recordUserNavigation;
    public int sampling_rate;
    public GameObject user;
    public UserNavigation userNavigation;
    public OdorMixer OdorMixer;
    public List<OdorObjectInstance> finalOdors;
    public List<OdorSourcePairs> odorSourcePairs;
    // Start is called before the first frame update
    void Start() {
        if (recordUserNavigation) userNavigation = new UserNavigation();
        if (user == null) user = Camera.main.gameObject;
        if (OdorMixer == null) OdorMixer = FindObjectOfType<OdorMixer>();
        InvokeRepeating("AddDataPoint", 0.0f, 0.5f);

        odorSourcePairs = new List<OdorSourcePairs>();
        foreach (OdorSource olf in FindObjectsOfType<OdorSource>()) {
            odorSourcePairs.Add(new OdorSourcePairs(olf.gameObject.name, olf.gameObject.transform.position, -1.0f));
        }
    }



    //private void Update() {
    //    if (recordUserNavigation)
    //        AddDataPoint();
    //}
    private void AddDataPoint() {
        userNavigation.userNavigationPoints.Add(
            new UserNavigationPoint(System.DateTime.Now,
                                    user.transform.position,
                                    OdorMixer.odorMixVector));
    }

    /// <summary>
    /// Add user selected object for User Study 3 Smell Profiles, invoked via UIListener.Confirm()
    /// </summary>
    public void AddUserResponse(GameObject selectedObject, bool user_selection, bool final = false) {
        bool isOdorObject = selectedObject.GetComponent<OdorSource>() == null ? false : true;
        UserSelection us = new UserSelection(selectedObject.transform.position,
                                            selectedObject.name,
                                            isOdorObject,
                                            user_selection,
                                            odorSourcePairs,
                                            final);
        userNavigation.userSelections.Add(us);
        Debug.Log($"Literal values {user_selection}");
    }

    public void SetFinal(List<OdorObjectInstance> occurences) {
        finalOdors = new List<OdorObjectInstance>();
        foreach (OdorObjectInstance odorInst in occurences) {
            finalOdors.Add(odorInst);
        }
    }

    /// <summary>
    /// Write data to disk
    /// </summary>
    public void SaveIntoJson() {
        string user_data = JsonUtility.ToJson(userNavigation);
        System.IO.File.WriteAllText(Application.persistentDataPath + "/" + subject_name + "_UserNavigation.json", user_data);
        Debug.Log("<color=green>" + Application.persistentDataPath + "/" + subject_name + "_UserNavigation.json" + "</color>");
    }

    //public void OnDisable() {
    //    if (recordUserNavigation) {
    //        AddFinalResponses();
    //        SaveIntoJson();
    //    }
    //}


    public void AddFinalResponses() {      
        foreach (OdorObjectInstance olfactoryObject in finalOdors) {
            AddUserResponse(olfactoryObject.gameObject, true, true);
        }
    }

    public void OnApplicationQuit() {
        if (recordUserNavigation) {
            AddFinalResponses();
            SaveIntoJson();
        }
    }
}

[System.Serializable]
public class UserNavigation {

    public List<UserNavigationPoint> userNavigationPoints;
    public List<UserSelection> userSelections;

    public UserNavigation() {
        userNavigationPoints = new List<UserNavigationPoint>();
        userSelections = new List<UserSelection>();
    }

    public UserNavigation(List<UserNavigationPoint> points) {
        userNavigationPoints = points;
    }
}

[System.Serializable]
public class UserNavigationPoint {
    public DateTime time;
    public Vector3 pos;
    public double[] odorFeatureVector;
    public UserNavigationPoint(DateTime dt, Vector3 vpos, OdorMixer.OdorMixVector cmv) {
        time = dt;
        pos = vpos;
        odorFeatureVector = new double[cmv.concentrationVector.Length];
        Array.Copy(cmv.concentrationVector, odorFeatureVector, cmv.concentrationVector.Length);
    }
}

[System.Serializable]
public class UserSelection {
    public Vector3 obj_pos;
    public string obj_name;
    public bool isOdorObject;
    public bool userResponse;
    public bool final;
    public List<OdorSourcePairs> odorSourcePairs;
    public UserSelection(Vector3 objp, string objn, bool odorous, bool response, List<OdorSourcePairs> odorPairs,  bool fnl = false) {
        obj_pos = objp;
        obj_name = objn;
        isOdorObject = odorous;
        userResponse = response;
        final = fnl;
        odorSourcePairs = new List<OdorSourcePairs>();
        foreach(OdorSourcePairs op in odorPairs) {
            odorSourcePairs.Add(new OdorSourcePairs(op.name, op.location, op.distance));    // ensure deep copy over shallow
        }
        for (int i=0; i<odorSourcePairs.Count; i++) {
            odorSourcePairs[i].distance = Vector3.Distance(obj_pos, odorSourcePairs[i].location);
        }
    }
}

[System.Serializable]
public class OdorSourcePairs {
    public string name;
    public Vector3 location;
    public float distance;
    public OdorSourcePairs(string n, Vector3 l, float d) {
        name = n;
        location = l;
        distance = d;
    }
}
