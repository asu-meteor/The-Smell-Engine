using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem;

public class MovePlayer : MonoBehaviour
{
    [Tooltip("Speed for W,A,S,D movement.")]
    public float moveSpeed = 4.5f;
    [Tooltip("Speed for dragging object around.")]
    public float speedH = 2.0f, speedV = 2.0f;
    // Every object instantiated with this class has a reference to UI manager
    // so that they may assign themselves as "Selected."
    public GameObject UI;
    private Vector3 moveDirection;
    private float yaw, pitch;
    private bool toggleUI;




    public void Awake() {

    }

    public void Start() {
        toggleUI = false;
        UI.SetActive(toggleUI);
    }

    void Update() {
        //if (Mouse.current.leftButton.IsPressed()) {
        //    ray = Camera.main.ScreenPointToRay(Mouse.current.position.ReadValue());
        //}        
        if (Mouse.current.rightButton.IsPressed()) {
            yaw += speedH * Mouse.current.delta.x.ReadValue();
            pitch -= speedV * Mouse.current.delta.y.ReadValue();
            transform.eulerAngles = new Vector3(pitch, yaw, 0.0f);
        }
        // UI toggling.
        //if (Input.GetKeyUp(KeyCode.T)) {
        //    toggleUI = !toggleUI;
        //    UI.SetActive(toggleUI);
        //}
        if (!EventSystem.current.IsPointerOverGameObject())
            CheckControls();
    }

    void CheckControls() {
        moveDirection = Vector3.zero;
        // Separate conditionals so multiple buttons can be held simultaneously.        
        if (Keyboard.current.wKey.IsPressed()) moveDirection += transform.forward;
        if (Keyboard.current.sKey.IsPressed()) moveDirection += -transform.forward;
        if (Keyboard.current.aKey.IsPressed()) moveDirection += -transform.right;
        if (Keyboard.current.dKey.IsPressed()) moveDirection += transform.right;
        transform.position += moveDirection.normalized * Time.deltaTime;
    }


}
