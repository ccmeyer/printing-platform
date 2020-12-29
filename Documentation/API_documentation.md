# Printing platform API documentation

## `Platform` class

* This is a class used to store the necessary variables required to operate the platform as well as handle all communication with the Dobot, Arduino and pressure regulator

### Dobot communication

`init_dobot()`
* Establishes the connection to the Dobot.
* Sets its movement parameters.
* Reads in the print calibration file which includes the locations of the loading and tube positions.
* Activates the gripper.

`get_plate_data()`
* Reads in the desired file path of the JSON file describing the plate information
* The information includes the well spacing, number of rows and columns and the positions of the four corner wells of the plate
* Generates a transformation matrix to get the corrected well XY-coordinates to ensure accurate Dobot positioning
* Finds the change in Z coordinates moving down the rows or across the columns and assumes a linear change in value to correct the Z coordinate for each well
* To create a new plate use the provided template in the 'Calibrations' directory
* Coordinates are stored as a dictionary with the three keys 'x', 'y', and 'z'

`write_plate_data()`
* Takes all of the current plate data and updates the metadata file that was originally loaded

`gen_trans_matrix()`
* Takes the location of the four corner wells and the plate dimensions and applies the `getPerspectiveTransform()` function from the OpenCV library to perform a four point transformation to map the actual location of the four wells to the expected location
* Then takes the inverse of the matrix so that it can be used to transform the expected coordinates of a well to the actual coordinates

`get_well_coords()`
* Take the desired row and column index and returns the corrected coordinates for the target well
* Uses the transformation matrix to take the expected coordinates and transform them into the real coordinates

`home_dobot()`
* First resets the Dobot's position to avoid having the arm hit the surrounding components during the homing process
* Runs the Dobot homing command
* Sets the location to the 'home' state
* This function should be called before performing any movements with the Dobot to ensure that it has its position correct

`move_dobot()`
* Takes XYZ coordinates and moves the Dobot to those coordinates

`dobot_manual_drive()`
* Drops into a manual drive mode controlled from the keyboard
* X direction is controlled using 'w' and 's'
* Y direction is controlled using 'a' and 'd'
* Z direction is controlled using 'k' and 'm'
* The step or amount that is moved is set using the 'f' to increase the step size and 'v' to decrease it. The step values are in mm
* To quit the manual drive mode, press 'q'

`change_print_position()`
* Initiates a protocol to modify the expected well locations of a given plate
* Moves from corner to corner and drops into `dobot_manual_drive()`to allow the operator to manually drive the Dobot to the correct location of each well to compensate for any deviations
* Once all the points are corrected, the new positions are stored in the plate metadata file.
* It is recommended to run this protocol prior to running any experiments to make sure that the positions are perfect
* Not that necessary for 96-well plates but should always be performed for 384-well plates
* The actual calibration protocol is described in detail [here]

`change_tube_position()`
* Moves to the currently saved tube position used during the printer head calibration protocol
* Drops into the `dobot_manual_drive()` mode to manual correct the position

`move_to_tube_position()`
* Moves to the currently saved tube position used during the printer head calibration protocol
* First moves above the tube to ensure that the arm does not hit the tube as it is located above the plate and the dobot uses point to point movement

`move_to_loading_position()`
* Moves to the currently saved loading position used during the printer head calibration protocol
* Used when switching out printer heads

`move_to_well(row,column)`
* Takes the desired row and column indexes and input and moves to the correct coordinates
* Checks to make sure that the target well is present in the plate

`load_gripper()`
* Initiates a protocol to open and close the gripper to make exchanging printer heads easier.

`disconnect_dobot()`
* Deactivates the gripper
* Disconnects from the Dobot

<br>

### Arduino communication

`init_ard()`
* Takes in the COM port of the Arduino and opens up serial communication
* Currently set to 'COM6' and would need to be changed to the correct COM port if that is incorrect

`print_droplets()`
* Takes the desired frequency, pulse width, refuel width, and droplet count for a printing command
* Serializes all the values and passes it to the Arduino and then pauses briefly
* Sends a second signal to the Arduino to confirm the end of transmission
* Waits to receive a signal from the Arduino that the printing protocol has been completed

`refuel_test()`
* Defined printing protocol used in calibration of the refuel process

`pulse_test()`
* Defined printing protocol used in calibration of the printing step

`refuel_open()`
* Opens the refuel valve and leaves it open

`pulse_open()`
* Opens the printing valve and leaves it open  

`close_valves()`
* Closes both valves

`close_ard()`
* Closes communication with the Arduino

<br>

### Pressure regulator communication

`init_pressure()`
* Initiates the Precigenome pressure regulator and the two channels used for refueling and printing

`set_pressure()`
* Takes in pressure values for the refuel and printing channels

`pressure_on()`
* Turns both pressure channels on

`pressure_off()`
* Turns both pressure channels off

`pressure_test()`
* Used to verify that the complete system is air tight
* Applies high pressure and records the flow
* If the flow rate is high that means that there is a leak in the system that needs to be addressed
* Load the gripper with position calibration chip so that the outlets that connect with the printer heads are seal to ensure proper seal
* The pressure test protocol is described in more detail [here]

`close_reg()`
* Closes communication with the pressure regulator

<br>

### Full platform functions

`initiate_all()`
* Opens communication with all three components

`drive_platform()`
* Comprehensive manually driving function
* Within this method, the operator is able to move the dobot by wells, load and unload the gripper, set and control pressures, and print defined arrays
* The exact functions executed by the drive function can be found in the print_platform_API.py file
* The key assignments can be easily changed to customize the use of drive function

`resistance_testing()`
* Initiates the printer head calibration protocol
* Creates a `PrinterHead` object and asks for the channel volume of the printer being used and then density of the reagent
* Sets the target droplet volume to 60 nL
* Monitors the refuel and printing steps and calculates the resistance of each component of the printer head
* A detailed description of this process can be found [here]

`print_array()`
* Takes a CSV file in the Print_arrays directory and prints the specified number of droplets into the target wells
* A template CSV file can be found in the Print_arrays directory

`disconnect_all()`
* Closes all communication with all three components

<br>

## `PrinterHead` class

* This is a class that is used to store all of the information associated with each printer head required for accurate printing with each printer head.
* Includes specifics about the reagent including its name and density and the printer head such as its overflow channel volume.
* It also contains all of the calibration information including the calculated resistances and the required pressures to print the desired droplet volume. 

<br>
