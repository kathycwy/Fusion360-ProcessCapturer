#Authors - Wing Yin Chan - Sai Limaye
#Description - MCP - A04 - Group 3

import adsk.core, adsk.fusion, adsk.cam, traceback
import math, random

# Global list to keep all event handlers in scope
handlers = []

def run(context):
    global app, ui
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        # Get the CommandDefinitions collection
        cmdDefs = ui.commandDefinitions
        
        # Create a button command definition
        CustomRingsButton = ui.commandDefinitions.addButtonDefinition('customRingsAddIn', 'Custom Rings', 'Create rings in different orientation', '')        
        createPanel = ui.allToolbarPanels.itemById('SolidCreatePanel')
        gearButton = createPanel.controls.addCommand(CustomRingsButton)
        
        if context['IsApplicationStartup'] == False:
            ui.messageBox('The "Custom Rings" command has been added\nto the CREATE panel of the MODEL workspace.')

        # Connect to the command created event
        customRingsCommandCreated = CustomRingsCommandCreatedEventHandler()
        CustomRingsButton.commandCreated.add(customRingsCommandCreated)
        handlers.append(customRingsCommandCreated)
        
        # Get the ADD-INS panel in the model workspace
        addInsPanel = ui.allToolbarPanels.itemById('SolidScriptsAddinsPanel')
        
        # Add the button to the bottom of the panel
        buttonControl = addInsPanel.controls.addCommand(CustomRingsButton)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# Event handler for the commandCreated event
class CustomRingsCommandCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
        
        # Get the command
        cmd = eventArgs.command

        # Get the CommandInputs collection to create new command inputs          
        inputs = cmd.commandInputs

        # Create radio buttons for choosing random / user-defined n
        radioButtonGroup = inputs.addRadioButtonGroupCommandInput('radioButtonInput', 'Number of rings (n)')
        radioButtonItems = radioButtonGroup.listItems
        radioButtonItems.add("Random", True)
        radioButtonItems.add("Custom", False)

        # Get user-defined n
        customN = inputs.addIntegerSpinnerCommandInput('customN', 'Input n (between 5 and 10)', 5, 10, 1, 5)
        inputs.itemById('customN').isEnabled = False

        # Create a check box to get if advanced seeting is wanted
        advancedSetting = inputs.addBoolValueInput('advancedSetting', 'Advanced setting',
                                               True, '', False)

        # Create radio buttons to get position preference
        customPosition = inputs.addDropDownCommandInput('customPosition', 'Position', adsk.core.DropDownStyles.TextListDropDownStyle)
        positionItems = customPosition.listItems
        positionItems.add("Straight", True)
        positionItems.add("Wave", False)
        inputs.itemById('customPosition').isVisible = False
        inputs.itemById('customPosition').isEnabled = False
        
        # Create dropdown to get orientation preference
        customOrientation = inputs.addDropDownCommandInput('customOrientation', 'Orientation', adsk.core.DropDownStyles.TextListDropDownStyle)
        orientationItems = customOrientation.listItems
        orientationItems.add('Standing', True)
        orientationItems.add('Lying', False)
        inputs.itemById('customOrientation').isVisible = False
        inputs.itemById('customOrientation').isEnabled = False

        # Create dropdown to get color preference
        customColor = inputs.addDropDownCommandInput('customColor', 'Color', adsk.core.DropDownStyles.TextListDropDownStyle)
        customColorItems = customColor.listItems
        customColorItems.add('Random', True)
        customColorItems.add('Custom', False)
        inputs.itemById('customColor').isVisible = False
        inputs.itemById('customColor').isEnabled = False

        # Get user-defined color (Red)
        customColorRed = inputs.addIntegerSpinnerCommandInput('customColorRed', 'Input Red (between 0 and 255)', 0, 255, 1, 0)
        inputs.itemById('customColorRed').isVisible = False
        inputs.itemById('customColorRed').isEnabled = False

        # Get user-defined color (Green)
        customColorGreen = inputs.addIntegerSpinnerCommandInput('customColorGreen', 'Input Green (between 0 and 255)', 0, 255, 1, 0)
        inputs.itemById('customColorGreen').isVisible = False
        inputs.itemById('customColorGreen').isEnabled = False

        # Get user-defined color (Blue)
        customColorBlue = inputs.addIntegerSpinnerCommandInput('customColorBlue', 'Input Blue (between 0 and 255)', 0, 255, 1, 0)
        inputs.itemById('customColorBlue').isVisible = False
        inputs.itemById('customColorBlue').isEnabled = False

        # Connect to the inputChanged event
        onInputChanged = CustomRingsCommandInputChangedHandler()
        cmd.inputChanged.add(onInputChanged)
        handlers.append(onInputChanged)
        
        # Connect to the execute event
        onExecute = CustomRingsCommandExecuteHandler()
        cmd.execute.add(onExecute)
        handlers.append(onExecute)


# Event handler for the inputChanged event
class CustomRingsCommandInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        eventArgs = adsk.core.InputChangedEventArgs.cast(args)
        
        # Get the changed input
        changedInput = eventArgs.input
        inputs = eventArgs.firingEvent.sender.commandInputs

        # Check if CustomN radio button is selected
        if changedInput.id == 'radioButtonInput':
            inputs.itemById('customN').isEnabled = not inputs.itemById('customN').isEnabled

        openColorRGB = False

        # Check if advancedSetting is checked
        if changedInput.id == 'advancedSetting':
            inputs.itemById('customPosition').isVisible = not inputs.itemById('customPosition').isVisible
            inputs.itemById('customPosition').isEnabled = not inputs.itemById('customPosition').isEnabled
            inputs.itemById('customOrientation').isVisible = not inputs.itemById('customOrientation').isVisible
            inputs.itemById('customOrientation').isEnabled = not inputs.itemById('customOrientation').isEnabled
            inputs.itemById('customColor').isVisible = not inputs.itemById('customColor').isVisible
            inputs.itemById('customColor').isEnabled = not inputs.itemById('customColor').isEnabled
            inputs.itemById('customColor').listItems[0].isSelected = True
            if (openColorRGB):
                inputs.itemById('customColorRed').isVisible = True
                inputs.itemById('customColorRed').isEnabled = True
                inputs.itemById('customColorGreen').isVisible = True
                inputs.itemById('customColorGreen').isEnabled = True
                inputs.itemById('customColorBlue').isVisible = True
                inputs.itemById('customColorBlue').isEnabled = True
            else:
                inputs.itemById('customColorRed').isVisible = False
                inputs.itemById('customColorRed').isEnabled = False
                inputs.itemById('customColorGreen').isVisible = False
                inputs.itemById('customColorGreen').isEnabled = False
                inputs.itemById('customColorBlue').isVisible = False
                inputs.itemById('customColorBlue').isEnabled = False

        # Check if customColor is checked
        if changedInput.id == 'customColor':
            openColorRGB = not openColorRGB
            inputs.itemById('customColorRed').isVisible = not inputs.itemById('customColorRed').isVisible
            inputs.itemById('customColorRed').isEnabled = not inputs.itemById('customColorRed').isEnabled
            inputs.itemById('customColorGreen').isVisible = not inputs.itemById('customColorGreen').isVisible
            inputs.itemById('customColorGreen').isEnabled = not inputs.itemById('customColorGreen').isEnabled
            inputs.itemById('customColorBlue').isVisible = not inputs.itemById('customColorBlue').isVisible
            inputs.itemById('customColorBlue').isEnabled = not inputs.itemById('customColorBlue').isEnabled



# Event handler for the execute event
class CustomRingsCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        eventArgs = adsk.core.CommandEventArgs.cast(args)

        # Get the values from the command inputs 
        inputs = eventArgs.command.commandInputs

        # Get the value of n
        if (inputs.itemById('radioButtonInput').listItems[0].isSelected):
            n = random.randint(5,10)
        else:
            n = int(inputs.itemById('customN').value)

        # By default, the rings are created in straight and standing manner, colors are random
        isShifted = False
        isStand = True
        isCustomColor = False
        red = 0
        green = 0
        blue = 0

        # Change the position, orientation and color accordingly
        if (inputs.itemById('advancedSetting').value == True):
            if (inputs.itemById('customPosition').listItems[1].isSelected):
                isShifted = True
            if (inputs.itemById('customOrientation').listItems[1].isSelected):
                isStand = False
            if (inputs.itemById('customColor').listItems[1].isSelected):
                isCustomColor = True
                red = int(inputs.itemById('customColorRed').value)
                green = int(inputs.itemById('customColorGreen').value)
                blue = int(inputs.itemById('customColorBlue').value)

        # Create the rings
        drawRings(n, isShifted, isStand, isCustomColor, red, green, blue)

        
        

def drawRings(n, isShifted, isStand, isCustomColor, red, green, blue):

    app = adsk.core.Application.get()

    ui  = app.userInterface

    product = app.activeProduct
    design = adsk.fusion.Design.cast(product)

    # Get the root component of the active design	
    rootComp = design.rootComponent

    if (isShifted):
        shift = 1
    else:
        shift = 0

    # Get a reference to an appearance in the library.
    lib = app.materialLibraries.itemByName('Fusion 360 Appearance Library')
    libAppear = lib.appearances.itemByName('Plastic - Matte (White)')

    try:
        for x in range(n):

            # Create a new sketch on the xy plane for standing rings; yz plane for lying rings	
            sketches = rootComp.sketches
            plane = rootComp.xYConstructionPlane
            if not (isStand):
                plane = rootComp.yZConstructionPlane
            sketch = sketches.add(plane)

            # Create a new ObjectCollection
            objColl = adsk.core.ObjectCollection.create()
            # Get the SketchCircles collection from an existing sketch
            circles = sketch.sketchCurves.sketchCircles

            # Call an add method on the collection to create a new circle
            if (isStand):
                circles.addByCenterRadius(adsk.core.Point3D.create(x*5, 0, shift), 2)
            else:
                circles.addByCenterRadius(adsk.core.Point3D.create(0, shift, x*12), 2)
            
            # Toggle the shift value
            shift *= -1

            # Get the SketchLines collection from an existing sketch
            lines = sketch.sketchCurves.sketchLines

            # Call an add method on the collection to create a new line
            if (isShifted and not isStand):
                axis = lines.addByTwoPoints(adsk.core.Point3D.create(-1,-4*shift,0), adsk.core.Point3D.create(1,-4*shift,0))
            else:
                axis = lines.addByTwoPoints(adsk.core.Point3D.create(-1,-4,0), adsk.core.Point3D.create(1,-4,0))

            # Get the first profile from the sketch
            prof = sketch.profiles.item(0)

            # Get the RevolveFeatures collection
            revolves = rootComp.features.revolveFeatures

            # Create a revolve input object that defines the input for a revolve feature
            revInput = revolves.createInput(prof, axis, adsk.fusion.FeatureOperations.NewComponentFeatureOperation)

            # Define a full revolve by specifying a specific revolve angle
            angle = adsk.core.ValueInput.createByReal(math.pi * 2 * (x+1) / n)
            revInput.setAngleExtent(False, angle)
                    
            # Create the revolve
            rev = revolves.add(revInput)

            comp = rev.parentComponent
            
            # Get the single occurrence that references the component.
            occs = rootComp.allOccurrencesByComponent(comp)
            occ = occs.item(0)
            
            # Create a copy of the existing appearance.
            newAppear = design.appearances.addByCopy(libAppear, 'Color ' + str(x+1))
            
            # Edit the "Color" property by setting it to a random color.
            colorProp = adsk.core.ColorProperty.cast(newAppear.appearanceProperties.itemByName('Color'))
            
            if not (isCustomColor) :
                red = random.randint(0,255)
                green = random.randint(0,255)
                blue = random.randint(0,255)

            colorProp.value = adsk.core.Color.create(red, green, blue, 0)  

            # Assign the new color to the occurrence.
            occ.appearance = newAppear
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def stop(context):
    try:
        createPanel = ui.allToolbarPanels.itemById('SolidCreatePanel')
        gearButton = createPanel.controls.itemById('adskSpurGearPythonAddIn')       
        if gearButton:
            gearButton.deleteMe()
        
        cmdDef = ui.commandDefinitions.itemById('adskSpurGearPythonAddIn')
        if cmdDef:
            cmdDef.deleteMe()
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
