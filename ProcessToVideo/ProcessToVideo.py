#Author-Wingyin Chan
#Description-Convert your creation process into video

import adsk.core, adsk.fusion, adsk.cam, traceback
import os

# Global list to keep all event handlers in scope
handlers = []

def run(context):
    try:
        global app, ui, product, design, timeline_var
        app = adsk.core.Application.get()
        ui  = app.userInterface
        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        timeline_var = design.timeline

        # Get the CommandDefinitions collection
        cmdDefs = ui.commandDefinitions
        
        # Create a command definition and add a button to the Add-ins panel.
        cmdDef = ui.commandDefinitions.addButtonDefinition('processToVideoAddIn', 
                                                            'ProcessToVideo', 
                                                            'Convert your creation process into video',
                                                            '')        
        addInsPanel = ui.allToolbarPanels.itemById('SolidScriptsAddinsPanel')
        addInsButton = addInsPanel.controls.addCommand(cmdDef)
        
        # Connect to the command created event.
        onCommandCreated = CommandCreatedEventHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        handlers.append(onCommandCreated)
        

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# Event handler for the commandCreated event
class CommandCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
        
        # Get the command
        cmd = eventArgs.command

        # Get the CommandInputs collection to create new command inputs          
        inputs = cmd.commandInputs

        # # Get user-defined n
        # durationN = inputs.addIntegerSpinnerCommandInput('durationN', 'Input n', 1, 10, 1, 1)

        # targetFolder = inputs.addTextBoxCommandInput('targetFolder', 'Target folder', '', 1, False)

        # Connect to the execute event
        onExecute = CommandExecuteHandler()
        cmd.execute.add(onExecute)
        handlers.append(onExecute)


# Event handler for the execute event
class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        eventArgs = adsk.core.CommandEventArgs.cast(args)

        # Get the values from the command inputs 
        inputs = eventArgs.command.commandInputs
        # # Get the value of n
        # n = int(inputs.itemById('durationN').value)
        # targetFolder = str(inputs.itemById('targetFolder'))

        # ui.messageBox("Save image to ", targetFolder)

        # Save image
        count = timeline_var.count
        timeline_var.moveToBeginning()
        while count>0 :
            filename = os.path.join("C:/Users/limaye/Desktop/Frames", "frame%s" % count)
            returnValue = timeline_var.movetoNextStep()
            app.activeViewport.saveAsImageFile(filename, 0, 0)  
            count = count-1

def stop(context):
    try:
        addInsPanel = ui.allToolbarPanels.itemById('SolidScriptsAddinsPanel')
        addInsButton = addInsPanel.controls.itemById('processToVideoAddIn')       
        if addInsButton:
            addInsButton.deleteMe()
        
        cmdDef = ui.commandDefinitions.itemById('processToVideoAddIn')
        if cmdDef:
            cmdDef.deleteMe()
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))