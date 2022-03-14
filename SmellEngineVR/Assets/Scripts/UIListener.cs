using Buttons.VR;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class UIListener : MonoBehaviour {
    //UIPanel is recieving (or subscribing) to gameobjects selected.
    public RecordUserNavigation recordUserNavigation;
    public GameObject menu;
    public Vector3 menuLocation;    
    public OdorObjectInstance objectInstance;
    //public int occurences;
    public List<OdorObjectInstance> occurences;

    public void Awake() {   if (recordUserNavigation == null) recordUserNavigation = FindObjectOfType<RecordUserNavigation>();  }

    public void Start() {
        occurences = new List<OdorObjectInstance>();
        OdorObjectInstance.OnSmellObjectInteracted += ActivateConfirmationPopUp;
    }

    void OnEnable() {
        if (recordUserNavigation == null) recordUserNavigation = FindObjectOfType<RecordUserNavigation>();        
    }

    void OnDisable() {  OdorObjectInstance.OnSmellObjectInteracted -= ActivateConfirmationPopUp;    }

    void ActivateConfirmationPopUp(GameObject odorObject) {
        objectInstance = odorObject.GetComponent<OdorObjectInstance>();      
        if (occurences.Count == 3 && !objectInstance.selected) return;
        Debug.Log($"On Smell Event selected:{odorObject.name}");


        menu.SetActive(true);
        Vector3 newPosition = odorObject.transform.position;
        newPosition.y += 1f;
        menu.transform.position = newPosition;
        ControllerRaycaster.selectedObject = odorObject;        
    }   

    /// <summary>
    /// Confirm Object invoked from Unity Button UI event.
    /// </summary>
    public void ConfirmedObject() {
        if (occurences.Count == 3) return;
        if (objectInstance != null)
            recordUserNavigation.AddUserResponse(objectInstance.gameObject, true);
        //objectInstance.GetComponent<Outline>().enabled = true;
        //objectInstance.GetComponent<OdorObjectInstance>().enabled = true;  // subject can no longer select
        objectInstance.EnableOutline();
        occurences.Add(objectInstance);
        recordUserNavigation.SetFinal(occurences);
        //objectInstance.GetComponent<ButtonController>().enabled = false;
    }

    /// <summary>
    /// Negate object invoked from Unity Button UI
    /// </summary>
    public void NegateObject() {
        recordUserNavigation.AddUserResponse(objectInstance.gameObject, false);
        objectInstance.DisableOutline();
        if (occurences.Count != 0) {
            occurences.Remove(objectInstance);
            recordUserNavigation.SetFinal(occurences);
        }
        //objectInstance.GetComponent<Outline>().enabled = false;
        //objectInstance.GetComponent<OdorObjectInstance>().enabled = false;  // subject can no longer select
    }

    /// <summary>
    /// Once user confirms button selection, this method closes the game object.
    /// </summary>
    public void DeactivateConifirmationPopUp() {
        Debug.Log("Menu is gone.");
        objectInstance = null;
        menu.transform.localPosition = menuLocation;
        ControllerRaycaster.selectedObject = null;
    }
}

