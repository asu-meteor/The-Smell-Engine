using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class FixedOlfactionTrigger : MonoBehaviour
{
    public delegate void EnteredSpace(OdorSource odor);
    public static event EnteredSpace OnEnteredSpace;
    public delegate void ExitedSpace(OdorSource odor);
    public static event ExitedSpace OnExitedSpace;

    public OdorSource odorSource;
    // Start is called before the first frame update
    void Start()
    {
        odorSource = transform.parent.gameObject.GetComponent<OdorSource>();
    }

    public void OnTriggerEnter(Collider other) {
        if (!other.gameObject.CompareTag("MainCamera")) return;
        OnEnteredSpace?.Invoke(odorSource);
    }

    public void OnTriggerExit(Collider other) {
        if (!other.gameObject.CompareTag("MainCamera")) return;
        OnExitedSpace?.Invoke(odorSource);
    }

}
