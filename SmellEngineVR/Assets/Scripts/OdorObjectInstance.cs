using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.InputSystem;

[RequireComponent(typeof(Outline))]
public class OdorObjectInstance : MonoBehaviour {
    public Outline objOutline;
    private GameObject odorObject;
    public bool selected;
    //OdorObjectInstance is Sending an event(s) to UIPanel.
    public delegate void SmellObjectInteracted(GameObject odorObject);
    public static event SmellObjectInteracted OnSmellObjectInteracted;
    // private bool firedEvent;

    // variable
    private void Start() {       
        if (objOutline == null) objOutline = GetComponent<Outline>();
        objOutline.enabled = false;
        odorObject = gameObject;
    }

    // Update is called once per frame
    void Update() {
        if (Keyboard.current.sKey.wasPressedThisFrame) {
            ControllerRaycaster.interactedObject = gameObject;
        }
        if (Keyboard.current.spaceKey.wasPressedThisFrame) {
            //ControllerRaycaster.selectedObject = gameObject;
            SelectedObject();
            Debug.Log("Press space");
        }

        //if (ControllerRaycaster.selectedObject != null &&
        //    ControllerRaycaster.selectedObject.Equals(gameObject)) {
        //    EnableOutline();
        //}
        //else if (ControllerRaycaster.interactedObject != null &&
        //    ControllerRaycaster.interactedObject.Equals(gameObject)) {
        //    //EnableOutline();           
        //} else {
        //    DisableOutline();
        //}
    }

    /// <summary>
    /// Invoked from Unity Editor 
    /// </summary>
    public void SelectedObject() {
        if (ControllerRaycaster.interactedObject == null || !(ControllerRaycaster.interactedObject.Equals(gameObject))) return;
        Debug.Log("Selected");
        OnSmellObjectInteracted?.Invoke(odorObject);
        //if (OnSmellObjectInteracted != null) {
        //    if (objOutline.enabled) {
        //        Debug.Log("Firing event");
        //        OnSmellObjectInteracted(odorObject);                
        //    }
        //}
    }
    public void EnableOutline() {
        objOutline.enabled = true;
        selected = true;
    }
    public void DisableOutline() {
        objOutline.enabled = false;
        selected = false;
    }

}