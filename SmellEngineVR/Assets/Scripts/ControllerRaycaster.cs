using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class ControllerRaycaster : MonoBehaviour {
    public static GameObject interactedObject;
    public static GameObject selectedObject;
    private Transform controllerPosition;


    void FixedUpdate() {
        InteractRaycast();
    }

    void InteractRaycast() {
        controllerPosition = gameObject.transform;
        Ray interactionRay = new Ray(controllerPosition.position, controllerPosition.forward);
        Vector3 interactionRayEndpoint = controllerPosition.forward * Mathf.Infinity;
        Debug.DrawLine(controllerPosition.position, interactionRayEndpoint, Color.green, 1.0f);

        //Debug.DrawLine(gameObject.transform.position, controllerPosition.forward*Mathf.Infinity, Color.green, 1.0f);
        if (Physics.Raycast(interactionRay, out RaycastHit interactionRayHit, Mathf.Infinity) &&
            (interactionRayHit.collider.CompareTag("Interactable"))) {
            //Debug.Log("Interacted Obj:\t" + interactionRayHit.collider.gameObject.name);
            interactedObject = interactionRayHit.collider.gameObject;
        } else {
            interactedObject = null;
        }
    }
}
