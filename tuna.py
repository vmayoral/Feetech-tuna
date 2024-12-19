import argparse
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from feetech_tuna import FeetechTuna

from servotemplates import servoTemplates


# Command line arts for port and baudrate
parser = argparse.ArgumentParser(description='Feetech Tuna - A tuning tool for Feetech servos')
parser.add_argument('port', type=str, help='The serial port to connect to')
parser.add_argument('--baudrate', type=int, default=1000000, help='The baudrate to use')
parser.add_argument('--servofamily', type=str, default="sms_sts", help='Servo family (sms_sts or scscl)')
parser.add_argument('--command', type=str, help='Direct command to execute (skips interactive mode)')

args = parser.parse_args()

# Prompt history
history = InMemoryHistory()

# Create a new FeetechTuna instance
tuna = FeetechTuna()

# Welcome message
print("Welcome to Feetech Tuna!")
print("-----------------------")
print("Connecting to port: " + args.port)

# Open the serial port
if tuna.openSerialPort(port=args.port, baudrate=args.baudrate, servoFamily=args.servofamily):
    print("Serial port opened successfully")
else:
    print("Failed to open the serial port - " + args.port)
    print("Exiting...")
    quit()

# Define function to handle commands
def handle_command(command, selectedServo):
    # Split commands by semicolon and strip whitespace
    commands = [cmd.strip() for cmd in command.split(";") if cmd.strip()]
    
    # Process each command in sequence
    for single_command in commands:
        should_exit = False
        
        if single_command == "exit" or single_command == "quit":
            return True, selectedServo  # Signal to exit immediately
        elif single_command == "list":
            list = tuna.listServos()
            print("Found " + str(len(list)) + " servos")
            for servo in list:
                print("Servo " + str(servo["id"]) + " - Model: " + str(servo["model"]))
        elif single_command.startswith("select"):
            parts = single_command.split(" ")
            if len(parts) == 2:
                selectedServo = int(parts[1])
                print("Selected servo: " + str(selectedServo))
            else:
                print("Usage: select <servo_id>")
        elif single_command == "deselect":
            selectedServo = None
            print("Deselected servo")
        elif single_command == "listregs":
            if selectedServo != None:
                regs = tuna.listRegs(selectedServo)
                for reg in regs:
                    print(str(reg["addr"]) + " " + reg["name"] + " = " + str(reg["value"]))
            else:
                print("No servo selected")
        elif single_command == "unlockeeprom":
            if selectedServo != None:
                tuna.unlockEEPROM(selectedServo)
            else:
                print("No servo selected")
        elif single_command == "lockeeprom":
            if selectedServo != None:
                tuna.lockEEPROM(selectedServo)
            else:
                print("No servo selected")
        elif single_command.startswith("writereg"):
            if selectedServo != None:
                parts = single_command.split(" ")
                if len(parts) == 3:
                    addr = int(parts[1])
                    value = int(parts[2])
                    tuna.writeReg(selectedServo, addr, value)
                else:
                    print("Usage: writereg <addr> <value>")
            else:
                print("No servo selected")
        elif single_command.startswith("readreg"):
            if selectedServo != None:
                parts = single_command.split(" ")
                if len(parts) == 2:
                    addr = int(parts[1])
                    tuna.readReg(selectedServo, addr)
                else:
                    print("Usage: readreg <addr>")
            else:
                print("No servo selected")
        elif single_command.startswith("setpos"):
            if selectedServo != None:
                parts = single_command.split(" ")
                if len(parts) == 2:
                    if (parts[1] == "min"):
                        minPos = tuna.readReg(selectedServo, 9)
                        tuna.writeReg(selectedServo, 42, minPos)
                    elif (parts[1] == "max"):
                        maxPos = tuna.readReg(selectedServo, 11)
                        tuna.writeReg(selectedServo, 42, maxPos)
                    else:
                        position = int(parts[1])
                        tuna.writeReg(selectedServo, 42, position)
                else:
                    print("Usage: setposition <position, min, max>")
            else:
                print("No servo selected")
        elif single_command.startswith("loadtemplate"):
            if selectedServo != None:
                parts = single_command.split(" ")
                if len(parts) == 2:
                    templateId = int(parts[1])
                    if templateId in servoTemplates:
                        
                        # Unlock the EEPROM
                        tuna.unlockEEPROM(selectedServo)

                        # Load the template values
                        success = True
                        template = servoTemplates[templateId]
                        for addr in template:
                            value = template[addr]
                            if (tuna.writeReg(selectedServo, addr, value) == False):
                                print("Failed to write register " + str(addr) + " - aborting template load")
                                success = False
                                break

                        # Set the servo ID last
                        if success:
                            tuna.writeReg(selectedServo, 5, templateId) # ID
                            print("Template loaded successfully")

                        # Switch to the new servo ID
                        selectedServo = templateId

                        # Lock the EEPROM
                        tuna.lockEEPROM(selectedServo)

                        # Read min position
                        minPos = tuna.readReg(selectedServo, 9)

                        # Move to min position
                        tuna.writeReg(selectedServo, 42, minPos)

                    else:
                        print("Unknown template: " + str(templateId))
                else:
                    print("Usage: loadtemplate <template_id>")
            else:
                print("No servo selected")
        else:
            print("Unknown command: " + single_command)
    
    return False, selectedServo  # Continue execution

# Modified main loop to handle both interactive and direct command modes
selectedServo = None
if args.command:
    # Direct command mode
    should_exit, selectedServo = handle_command(args.command, selectedServo)
else:
    # Interactive mode
    while True:
        if (selectedServo == None):
            pmsg = ">> "
        else:
            pmsg = "(Servo " + str(selectedServo) + ") >> "

        command = prompt(pmsg, history=history)
        should_exit, selectedServo = handle_command(command, selectedServo)
        if should_exit:
            break

# Close the serial port
tuna.closeSerialPort()
print("Serial port closed")
print("Exiting...")



