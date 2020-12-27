# uCD microfluidic printing system
### A system for high throughput reaction generation using sub-microliter printing

<br/>

## Overview
The system detailed in this repository was originally described in the paper: "__________". This repository includes the necessary components to recreate the system shown in **Figure 1**. This repository includes the following components:
* Description of the underlying theory behind the system and how to optimize its use [link]
* A parts list and CAD files to 3D print or laser cut the required components to assemble the system [link]
* Scripts required to control all components of the system [link]

<br/>

## Printing platform

<p align="center">
  <img src="./Images/printing_platform_overview.png?raw=true" title="uCD printing system">
</p>

<p align="center">
  <strong>Figure 1</strong> Diagram of the complete printing platform. (A) Image of the full platform, 1) 12.5V DC power supply, <br>2) Dobot robotic arm, 3) Precigenome pressure regulator, 4) Analytical balance, 5) Gripper holding a printer head, <br>6) Valve control circuit, 7) Arduino Uno microcontroller, 8) Well plate. (B) Close up of the printer head positioned <br>over the reagent tube during calibration. (C) Dobot gripper with the 3D printed gripper adapters holding <br>a printer head. (D) Valve control circuit connected to an Arduino
</p>

The core of the μCD system is a disposable multilayer microfluidic container composed of a 3D printed reservoir linked to a microfluidic printing nozzle with two pneumatic control channels that can be reversibly connected to a robotic arm. This robotic arm is customized to enable reliable linking between the pneumatic controllers and the microfluidic device. The modular and disposable design of the μCD system allows for the inclusion of limitless reagents in a multicomponent experiment as the microfluidic devices are can be swapped in and out without risk of cross-contamination.

The printing platform is comprised of several critical components:
* The three-dimensional positioning and loading of printer heads are achieved using the Dobot magician robotic arm with the gripper attachments. 
* The printing and refuel pressures are regulated by the Precigenome pressure regulator. 
* The Arduino and valves are used to apply the pressures in bursts for printing and refueling.
* The storage and printing is carried out in the disposable microfluidic printing heads.

A detailed description of the components and assembly can be found [here]

<br/>

## Printing concept

<p align="center">
  <img src="./Images/printer_head_design.png" width="800" title="Printer head design">
</p>

<p align="center">
  <strong>Figure 2</strong> Schematic depicting the printer head design. A) Labels the components of the printer head. B) Overlay of <br>the parameters of the system. Tunable parameters: purple, fixed parameters: red, unknown parameters: black.
</p>

The system is built upon microfluidic adaptive printing where when force, in this case pressure, is applied to liquid in small bursts it forces the liquid to be ejected through a small exit port (<100 um) as nanoliter sized droplets. 

<br/>

## Platform API

<p align="center">
  <img src="./Images/valve_control_circuit.png?raw=true" width="350" title="Valve control circuit">
</p>

