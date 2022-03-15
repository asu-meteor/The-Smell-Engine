# The Smell Engine

[**Project Page**](https://meteor.ame.asu.edu/projects/smell-engine/)  |  [**Video**](https://www.youtube.com/watch?v=vV36-LQbsOU)  | [**Paper**](https://meteor.ame.asu.edu/publications/SmellEngineIEEEVRR22.pdf)

[The Smell Engine: A system for artificial odor synthesis in virtual environments](https://meteor.ame.asu.edu/projects/smell-engine/)  
 [Alireza Bahremand](https://www.alirezabahremand.com/)<sup>1</sup>,
 [Mason Manetta](https://mcmanetta.github.io)<sup>1</sup>,
 [Jessica Lai](https://github.com/jmklai)<sup>1</sup>,
 [Byron Lahey](https://herbergerinstitute.asu.edu/profile/byron-lahey)<sup>1</sup>,
 [Christy Spackman](http://www.christyspackman.com/)<sup>1</sup>,
 [Brian H. Smith](https://isearch.asu.edu/profile/843330)<sup>1</sup>,
 [Richard C. Gerkin](https://rick.gerk.in/about/)<sup>1</sup>,
 [Robert LiKamWa](https://meteor.ame.asu.edu/)<sup>1</sup><br>
 <sup>1</sup>Arizona State University
in IEEE VR 2022 (Oral Presentation)

## What is the Smell Engine?
The Smell Engine is a system for designing virtual odor-infused environments and generating olfactory stimuli within the virtual environment by controlling an olfactory display. More info can be found [here](https://meteor.ame.asu.edu/projects/smell-engine/)

This system can be run as a CLI or Virtual Reality (VR) experience. 
To run as a CLI interface, the notebooks provide documented examples.
To run as a VR experience, the Smell Engine VR directory contains an example Unity project.

## Install:
In the root directory, run: ```pip install requirements.txt```

## Documentation:
Documentation for the framework can be found [here](https://asu-meteor.github.io/The-Smell-Engine/html/index.html)

## Presentations:
The Smell Engine: A system for artificial odor synthesis in virtual environments (March, 2022) </br>
https://youtu.be/vV36-LQbsOU

CHI Smell Taste, Temperature, Touch Workshop (April, 2021) </br>
https://www.youtube.com/watch?v=zbZQZc74ZuA


## Notebook/CLI Interface 
In the notebooks directory, there are a various Jupyter notebooks demonstrating PID testing, olfactometer control scheduling, and odor table generating. 

## Virtual Reality + Unity 3D
In the Smell Engine VR directory, an example Unity (2019.4.2X) project provides the Odor Source and Odor Mix modules. The olfactometer directory contains the olfactometer control scripts which must be run before the VR experience. 

To start, run </br>
```$ python smell_engine_communicator.py [DEBUG_MODE] [ODOR_TABLE_MODE] [WRITE_DATA]```

- ```[DEBUG_MODE]``` is a flag specifying whether the olfactometer is physically connected or should be simulated.
- ```[ODOR_TABLE_MODE]``` is a parameter for specifying the path to a odor table pkl file. 
- ```[WRITE_DATA]``` is a flag specifying whether data should be saved to JSON for session.

For more information on flags, simply run </br>
```$ python smell_engine_communicator.py --help```

Then, run the Unity scene. Unity will transmit the odorant PubChemIDs, intitialize the system modules, and perform an initial system configuration. Upon successful connection, the command line console should look as follows:
<p float="left">
    <img src="https://i.imgur.com/eeNavtp.png" width="350" height="333"/>    
</p>

---

To design a virtual olfactory space, simply assign a Odor Source component and specify it's PubChemID as follows:

<p float="left">
    <img src="https://i.imgur.com/wkRPxHq.gif" width="350" height="219"/>    
    <!-- <img src="https://i.imgur.com/rZBlSLV.gif" width="350" height="219"/>     -->
</p>

## How it works:

### Smell Engine Pipeline
We devise a software-hardware framework that integrates olfactory stimuli into virtual environments, such that odor strengths spatiotemporally vary based on user navigation and interaction, presenting odors through a mask-based apparatus. 

The Smell Engine achieves this using design-time operations and runtime operations. Design time operations involve the Odor Source interface and runtime operations involve the Smell Mixer, Smell Controller, and Valve Driver.

<p float="left">
    <img src="https://i.imgur.com/cScXc9o.png" width="750" height="115"/>    
</p>


---

<!-- #### PubChem Interface -->
<!-- --- -->

### Odor Source Interface
The Odor Source Component lets developers specify
a feature vector of odorant-specific concentrations and dispersion constants to configure odor "flavor", "strength", and propagation of each odor source.

<p float="left">
    <img src="https://i.imgur.com/WGpZD15.jpg" width="350" height="225"/>    
</p>

---
### Smell Mixer Component
The Smell Mixer component dynamically estimates the odor mix that the user would smell, based on odor source distances and diffusion models.

---

### Smell Controller Module
The Smell Controller coordinates a hardware olfactometer to physically present an approximation of the odor mix to the user’s mask from a set of odorants channeled through controllable flow valves. 

Currently, developers can pre-compute the Olfactometer hardware states for a virtual odor space configuration, or perform calculations on-the-fly using a series of linear and non-linear solvers.

<p float="left">
    <img src="https://i.imgur.com/MIQITv6.jpg" width="350" height="84"/>    
</p>

---

### Valve Driver Module
The Valve Driver component issues multiplexed digital and analog signals that correspond to scheduled valve states and MFC flow rate setpoints.

We implemented our Valve Driver component using NIDAQmx SDK, which is included as a sub-directory for this repository.

<p float="left">
    <img src="https://i.imgur.com/RfQOkDW.png" width="350" height="312"/>    
</p>

---

## Known Issues

* Receiving PubChem API data can take ~30 seconds. Proposed solution is to save data to JSON and allow user to pass odorant properties as JSON input.

## Planned Features

* Serial communication support.
* Odorant Molecule name parameter. Currently, Odor Source configuration requires the PubChemID. The code is implemented for this feature, and is currently under testing.

## Citation

```
@inproceedings{alireza2022_SmellEngine,
  title={The Smell Engine: A system for artificial odor synthesis in virtual environments},
  author={Alireza Bahremand and Mason Manetta and Jessica Lai and Byron Lahey and Christy Spackman and Brian H. Smith and Richard C. Gerkin and Robert LiKamWa},
  booktitle={2022 IEEE Virtual Reality and 3D User Interfaces (VR)},
  year={2022}
}
```

## License
<!-- Released under the [MIT license](LICENSE). -->

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

The MIT License (MIT)

Copyright © 2022 Alireza Bahremand, Mason Manetta, Jessica Lai, Richard C. Gerkin, Robert LiKamWa

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


<!-- ### License

Copyright © 2022, [Alireza Bahremand](https://github.com/TheWiselyBearded).
Released under the [MIT license](LICENSE). -->
