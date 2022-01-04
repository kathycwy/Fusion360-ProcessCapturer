#Author-Wingyin Chan, Sai Limaye
#Description-Convert your creation process into video

import adsk.core, adsk.fusion, adsk.cam, traceback
import os,sys
# import pip
# import subprocess
# import numpy as np
# import glob

#get the path of add-in
my_addin_path = os.path.dirname(os.path.realpath(__file__)) 

#add the path to the searchable path collection
if not my_addin_path in sys.path:
    sys.path.append(my_addin_path) 

import cv2

# Global list to keep all event handlers in scope
handlers = []
filenames = []
timeline_names = []
img_array = []
operations = []
operatingPlatform = ""

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
    
        operatingPlatform = getPlatform()
       
        #Define inputs for Windows
        if operatingPlatform == "Windows":
            filename = inputs.addStringValueInput('videoname', 'Video name')
            targetFolder = inputs.addTextBoxCommandInput('targetFolder', 'Save directory', '', 1, False)
            selectFolderBtn = inputs.addBoolValueInput('selectFolderBtn', 'Select', False, '', False)
            rotate = inputs.addBoolValueInput('rotate', 'Rotate Design?', True, '')
            skip = inputs.addBoolValueInput('skip', 'Include all steps?', True, '')
            background = inputs.addBoolValueInput('background', 'Add background?', True, '')
            range = inputs.addIntegerSliderCommandInput('range', 'Timeline Range', 1, 100, True)
            range_start = inputs.itemById('range').valueOne
            range_end = inputs.itemById('range').valueTwo

        #Define inputs for MacOS
        if operatingPlatform == "MacOS":
            filename = inputs.addStringValueInput('imagename', 'Image name')
            targetFolder = inputs.addTextBoxCommandInput('targetFolder', 'Save directory', '', 1, False)
            selectFolderBtn = inputs.addBoolValueInput('selectFolderBtn', 'Select', False, '', False)

        # Connect to the inputChanged event
        onInputChanged = CommandInputChangedHandler()
        cmd.inputChanged.add(onInputChanged)
        handlers.append(onInputChanged)

        # Connect to the execute event
        onExecute = CommandExecuteHandler()
        cmd.execute.add(onExecute)
        handlers.append(onExecute)

# Event handler for the inputChanged event
class CommandInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        eventArgs = adsk.core.InputChangedEventArgs.cast(args)
        
        # Get the changed input
        changedInput = eventArgs.input
        inputs = eventArgs.firingEvent.sender.commandInputs
    
        # Check if select folder button is selected
        if changedInput.id == 'selectFolderBtn':
            if inputs.itemById('selectFolderBtn').value:
                # Set styles of file dialog.
                folderDlg = ui.createFolderDialog()
                folderDlg.title = 'Fusion Choose Folder Dialog' 
                
                # Show folder dialog
                dlgResult = folderDlg.showDialog()
                if dlgResult == adsk.core.DialogResults.DialogOK:
                    inputs.itemById('targetFolder').text = folderDlg.folder
                else:
                    return


# Event handler for the execute event
class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        eventArgs = adsk.core.CommandEventArgs.cast(args)
   
        # Get the user inputs
        inputs = eventArgs.command.commandInputs
        operatingPlatform = getPlatform()

        if operatingPlatform == "Windows":
            videoname = inputs.itemById('videoname').value
            targetFolder = inputs.itemById('targetFolder').text
            ui.messageBox(targetFolder)
            rotate = inputs.itemById('rotate').value
            skip = inputs.itemById('skip').value
            background = inputs.itemById('background').value
            start = inputs.itemById('range').valueOne
            end = inputs.itemById('range').valueTwo

            # Save image
            count = timeline_var.count + 1 
            timeline_var.moveToBeginning()

            for index in range(1, count) :
                #Take screenshot of timeline step and save it in specified path
                frame = "frame%s" % index
                filename = os.path.join(targetFolder, frame)
                filenames.append("%s.png" % filename)   
                entity = timeline_var.item(index-1).entity        
                timeline_step = type(entity).__name__

                if timeline_step == 'Sketch' or timeline_step == 'ConstructionPlane' or timeline_step == 'ConstructionPoint' or timeline_step == 'ConstructionAxis' or timeline_step == 'ThreadFeature' or timeline_step == 'Combine' or timeline_step=='Occurrence':
                    if skip==True:
                        continue
                    else:
                        size = saveImage(entity,targetFolder,timeline_step,frame,filename) 
                else:
                    size = saveImage(entity,targetFolder,timeline_step,frame,filename)    
        
    
            #Create video and save in target folder
            name = targetFolder+'/'+videoname+'.mp4'
            out = cv2.VideoWriter(name,cv2.VideoWriter_fourcc(*'DIVX'), 1, size)
            for i in range(len(img_array)):
                out.write(img_array[i])
            out.release()

            # Display finish message
            ui.messageBox(str(timeline_var.count) + ' snapshots are taken.\nProcess video '+videoname+'.mp4 is saved to [' + targetFolder + '].')

        if operatingPlatform == "MacOS":
            imagename = inputs.itemById('imagename').value
            targetFolder = inputs.itemById('targetFolder').value


def saveImage(entity,targetFolder,timeline_step,frame,filename):
    timeline_names.append(timeline_step)
    timeline_operation = getOperations(entity)
    operations.append(timeline_operation)

    returnValue = timeline_var.movetoNextStep()
    app.activeViewport.saveAsImageFile(filename, 0, 0)  

    #Add timeline step text to image
    path = '%s' % targetFolder+'/%s' % frame+'.png'
    img = cv2.imread(path)      
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img, '%s' % timeline_step, (10,400), font, 3, (0, 0, 0), 2, cv2.LINE_AA) 
    cv2.putText(img, '%s' % timeline_operation, (10,450), font, 2, (0, 0, 0), 2, cv2.LINE_AA) 
    cv2.imwrite(path, img)
    height, width, layers = img.shape
    size = (width,height)
    img_array.append(img)

    return size

def getPlatform():
    #Check OS
    from sys import platform
    if platform == "linux" or platform == "linux2":
        ui.messageBox('Sorry this add-in does not support Linux system.')
        return "Linux"
    elif platform == "darwin":
        ui.messageBox("Only limited features are available on MacOS.")
        return "MacOS"
    elif platform == "win32":
        return "Windows"
    ui.messageBox("Sorry this add-in does not support your operating system.")
    return "error"

def getOperations(entity):
    classname = type(entity).__name__
    param = ''

    if classname == 'ExtrudeFeature':
        distance = round(entity.extentOne.distance.value * 10, 2)
        param = ' - distance ' + str(distance) + ' mm'

    if classname == 'RevolveFeature':
        angle = round(entity.extentDefinition.angle.value, 2)
        param = ' - angle ' + str(angle) + ' rad'

    if classname == 'FilletFeature':
        edgeSets = entity.edgeSets
        for edgeSet in edgeSets:
            if (type(edgeSet).__name__ == 'ConstantRadiusFilletEdgeSet'):
                constantEdgeSet = adsk.fusion.ConstantRadiusFilletEdgeSet.cast(edgeSet)
                radius = constantEdgeSet.radius.expression
                param = ' - radius type: constant - radius ' + str(radius)
            if (type(edgeSet).__name__ == 'VariableRadiusFilletEdgeSet'):
                variableEdgeSet = adsk.fusion.VariableRadiusFilletEdgeSet.cast(edgeSet)
                startRadius = round(variableEdgeSet.startRadius.value * 10, 2)
                endRadius = round(variableEdgeSet.endRadius.value * 10, 2)
                param = ' - radius type: variable - startRadius ' + str(startRadius) + ' mm & endRadius ' + str(endRadius) + ' mm'
            if (type(edgeSet).__name__ == 'ChordLengthFilletEdgeSet'):
                chordLengthEdgeSet = adsk.fusion.ChordLengthFilletEdgeSet.cast(edgeSet)
                chordLength = round(chordLengthEdgeSet.chordLength.value * 10, 2)
                param = ' - radius type: chord length - chord length ' + str(chordLength) + ' mm'
    
    if classname == 'HoleFeature':
        diameter = round(entity.holeDiameter.value * 10, 2)
        param = ' - diameter ' + str(diameter) + ' mm'

    if classname == 'ShellFeature':
        insideThickness = round(entity.insideThickness.value * 10, 2)
        outsideThickness = entity.outsideThickness
        param = ' - insideThickness ' + str(insideThickness) + ' mm & outsideThickness ' + str(outsideThickness) + ' mm'

    return param

       

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
