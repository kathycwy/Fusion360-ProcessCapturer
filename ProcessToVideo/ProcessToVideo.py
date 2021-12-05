#Author-Wingyin Chan
#Description-Convert your creation process into video

import adsk.core, adsk.fusion, adsk.cam, traceback
import os
import pip
import subprocess
import sys

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

        # Get user inputs
        speed = inputs.addIntegerSpinnerCommandInput('speed', 'Speed', 1, 10, 1, 1)
        targetFolder = inputs.addTextBoxCommandInput('targetFolder', 'Save directory', '', 1, False)

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

        # Get the user inputs
        speed = int(inputs.itemById('speed').value)
        targetFolder = inputs.itemById('targetFolder').text

        # Save image
        count = timeline_var.count
        filenames = []
        timeline_var.moveToBeginning()
        while count>0 :
            filename = os.path.join(targetFolder, "frame%s" % count)
            filenames.append("%s.png" % filename)
            returnValue = timeline_var.movetoNextStep()
            app.activeViewport.saveAsImageFile(filename, 0, 0)  
            count = count-1

        res = [f.replace('', '/') for f in filenames]
        subprocess.check_call([sys.executable, "-m", "pip", "install", "imageio"])  
        import imageio
        images = []
       
        for filename in filenames:
            images.append(imageio.imread(filename))
       
        imageio.mimsave('%s/movie.gif' % targetFolder, images)
       
        # Display finish message
        ui.messageBox(str(timeline_var.count) + ' snapshots are taken.\nProcess video name.mp4 is saved to [' + targetFolder + '].')
        

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
