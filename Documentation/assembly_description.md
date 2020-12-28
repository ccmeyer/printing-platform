# Printing platform assembly

<p align="center">
  <img src="../Images/printing_platform_overview.png?raw=true" title="&#181;CD printing system">
</p>

<p align="center">
  <strong>Figure 1</strong> Diagram of the complete printing platform. (A) Image of the full platform, 1) 12.5V DC power supply, <br>2) Dobot robotic arm, 3) Precigenome pressure regulator, 4) Analytical balance, 5) Gripper holding a printer head, <br>6) Valve control circuit, 7) Arduino Uno microcontroller, 8) Well plate. (B) Close up of the printer head positioned <br>over the reagent tube during calibration. (C) Dobot gripper with the 3D printed gripper adapters holding <br>a printer head. (D) Valve control circuit connected to an Arduino
</p>

The printing platform is comprised of several different components. The three-dimensional positioning and loading of printer heads are achieved using the Dobot magician robotic arm with the gripper attachments. The printing and refuel pressures are regulated by the Precigenome pressure regulator. The Arduino and valves are used to apply the pressures in bursts for printing and refueling. The assembled system is shown in **Figure 1**. 

## Material list

1.	PMMA sheets (75 μm thick)
2.	Double-sided adhesive membrane (ARcare 90445, Adhesives Research, 80 μm thick)
3.	CO2 laser cutter (Universal Laser Systems, VersaLaser 2.30)
4.	85 μm nozzle in 75 μm thick PMMA (Jestar Mold Tech Co., Ltd)
5.	SLA 3D printer (Form 3 Formlabs)
6.	Clear Resin (Formlabs)
7.	Analytical Balance (U.S Solid 1mg or ideally 0.1mg precision)
8.	Robotic arm (Dobot Magician)
9.	Two mini solenoid valves (LHDA1221111H, Lee Co)
10.	Manifold (Lee Co.)
11.	Automated pressure regulator (Precigenome Pressure/Flow controller light version, PG-MFC-LT2CH-X)
12.	Microcontroller (Arduino Uno)
13.	12.5V Power supply (BK precision programmable DC power supply)
14.	Thin tubing (1/16” and 1/8” Tygon® S3™ E-3603 Non-DEHP Laboratory Tubing)
15	Diode 1N4005
16.	Zener Diode 1N4757 51V
17.	Transistor MJH11022G
18.	Resistor 330 Ω
19.	Connector wires
20.	Breadboard


## Steps to assembe the platform

1. Connect the gripper attachment to the Dobot 

2. 3D print and attach the 3D printed gripper adapters, shown in **Figure 2**, to the end effector.

<p align="center">
  <img src="../Images/Gripper_attachment.png?raw=true" width="350" title="Gripper attachments">
</p>

<p align="center">
  <strong>Figure 2</strong> Gripper adapters used to accurately grip the printer heads
</p>

2. Screw each valve into the manifold and attach it to Dobot near the gripper (see Note 11).

3. Connect the gripper adapters to the manifolds using the thin tubing. Then connect the manifolds to the corresponding pressure outlets on the Precigenome pressure regulator.

4. Construct the circuit shown in **Figure 3** and connect the Arduino, the two valves and the power source to it Provide enough extra tubing and wires to run them along the arm to not restrict its motion while in use.

<p align="center">
  <img src="../Images/valve_control_circuit.png?raw=true" width="350" title="Valve control circuit">
</p>

<p align="center">
  <strong>Figure 3</strong> Circuit design used to regulate the valves controlling the pressure flow using the Arduino
</p>

5.	Set the voltage of the power source to 12.0 V or the required voltage for the valves.

6.	Laser cut the provided [template] and place around the Dobot to provide consistent placement of the well plate and balance in the Dobot’s Cartesian coordinate system.

7.	Connect the arm, the pressure regulator, and the Arduino to your computer.

8.	Upload the provided Arduino program to the Arduino provided [here].

9.	3D print the tube stand and place on top of the scale.

## Steps to assemble the printer heads

1.	To fabricate the layer with the small nozzle, a UV-laser is used to ablate a small hole (65-85µm diameter) into a PMMA sheet. A range of nozzle diameters can be used to give different size droplets. The nozzles can be fabricated by the following companies: Jestar Mold Tech Co., Ltd (China) and Micron Laser Technology Inc. (USA).

2.	The channel layer can be fabricated using a CO2 laser to ablate microchannels in double-sided membrane adhesive. The chosen channel width was 200 μm.	A wide range of channel widths and lengths can be used. Choose the width based on the desired channel resistance. 

3.	The bulk component of the printer head, which contains the connections to the pressure inlets and the reagent reservoir, is fabricated by 3D printing (see Note 16). We used stereolithography (SLA) printing with surgical guide photosensitive resin to generate the printer heads and the gripper adapters. It is critical that these printer heads are watertight, transparent and have smooth channels for proper use. These qualities are very difficult to achieve with standard fused deposition modeling (FDM) printers as there are many imperfections at the junctions between layers.

4.	The full printer head is assembled stepwise:

5.	Peel one side from the adhesive layer containing the channel and adhere it to the bottom of the 3D printed component. Line up the entry and exit holes of the channel with the corresponding openings on the 3D printed part.

6.  Peel off the other side of the adhesive layer and place the nozzle layer on top. Ensure that the small nozzle is lined up with the exit of the channel. Firmly press the layers down to make sure that there are no air pockets.





