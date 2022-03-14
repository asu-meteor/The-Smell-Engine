using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.XR;

public class XR_Movement : MonoBehaviour {
    public float speed;
    UnityEngine.XR.InputDevice controller;
    // Start is called before the first frame update
    void Start() {
        speed = 0.5f;
        var gameControllers = new List<UnityEngine.XR.InputDevice>();
        UnityEngine.XR.InputDevices.GetDevicesWithRole(UnityEngine.XR.InputDeviceRole.RightHanded, gameControllers);
        foreach (var device in gameControllers) {
            Debug.Log(string.Format("Device name '{0}' has role '{1}'", device.name, device.role.ToString()));
        }
        if (gameControllers.Count > 0) {
            controller = gameControllers[0];
        }
    }

    // Update is called once per frame
    void Update() {
        bool triggerValue;

        if (controller.TryGetFeatureValue(CommonUsages.triggerButton, out triggerValue) && triggerValue) {
            transform.Translate(Camera.main.transform.forward * speed);
        }
        if (controller.TryGetFeatureValue(CommonUsages.gripButton, out triggerValue) && triggerValue) {
            //transform.Translate(Camera.main.transform.up * speed);
            gameObject.transform.localPosition += new Vector3(0, 3, 0);
        }

    }
}
