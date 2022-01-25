# Author - Wingyin Chan, Sai Limaye
# Description - Convert your creation process into images/video

import cmd
from json import tool
import adsk.core, adsk.fusion, adsk.cam, traceback
import os,sys
import time

# Get the path of add-in
my_addin_path = os.path.dirname(os.path.realpath(__file__)) 

# Add the path to the searchable path collection
if not my_addin_path in sys.path:
    sys.path.append(my_addin_path) 

# Global lists to keep all event handlers and variables in scope
handlers = []
filenames = []
timeline_names = []
img_array = []
operations = []


def run(context):
    try:
        global app, ui, product, design, timeline_var
        app = adsk.core.Application.get()
        ui  = app.userInterface
        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        timeline_var = design.timeline
  
        # Create new tab tbPanel in toolbar 
        workSpace = ui.workspaces.itemById('FusionSolidEnvironment')
        tbPanels = workSpace.toolbarPanels
        pcPanel = tbPanels.itemById('ProcessCapturerPanel')
        if pcPanel:
            pcPanel.deleteMe()
        pcPanel = tbPanels.add('ProcessCapturerPanel', 'Process Capturer', 'SelectPanel', False)

        # Get the CommandDefinitions collection
        cmdDefs = ui.commandDefinitions
        
        # Create command definition for our add-in
        buttonTooltip = 'Convert your creation process into images/video'
        cmdDef = ui.commandDefinitions.addButtonDefinition('processCapturerAddIn', 
                                                            'Process Capturer', 
                                                            buttonTooltip,
                                                            './Resources/icon')  
        tooltip = "./Resources/tooltip/tooltip.png"
        cmdDef.toolClipFilename =  tooltip
       
        # Add button to new ProcessCapturerPanel
        pcPanel = ui.allToolbarPanels.itemById('ProcessCapturerPanel')
        addInsButton = pcPanel.controls.addCommand(cmdDef)

        # Add button to original SolidScriptsAddinsPanel
        addInsPanel = ui.allToolbarPanels.itemById('SolidScriptsAddinsPanel')
        addInsButton = addInsPanel.controls.addCommand(cmdDef)
        
        # Connect to the commandCreated event.
        onCommandCreated = CommandCreatedEventHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        handlers.append(onCommandCreated)

        ui.messageBox('ProcessCapturer has been added under UTILITIES tab.')

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


######################################## FUSION EVENT HANDLERS ########################################

# Event handler for the commandCreated event
class CommandCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)

        # Get and set the command 
        cmd = eventArgs.command
        cmd.setDialogMinimumSize(600,300)
        cmd.setDialogInitialSize(600,300)

        # Get the CommandInputs collection to create new command inputs          
        inputs = cmd.commandInputs

        # Print msg then end the add-in when the design is empty
        if timeline_var.count == 0:
            ui.messageBox("Your design is empty, nothing can be captured. Please create a model then try our capturer again.")
            return
        
        global operatingPlatform 
        operatingPlatform = getPlatform()

        # Save the current camera view for later restoring
        global currentCamera
        currentCamera = app.activeViewport.camera
      
        # Define inputs for Windows
        if operatingPlatform == "Windows":
            videoname = inputs.addStringValueInput('videoname', 'Name*')
            selectFolderBtn = inputs.addBoolValueInput('selectFolderBtn', 'Select folder*', False, './Resources/button', False)
            targetFolder = inputs.addTextBoxCommandInput('targetFolder', 'Save directory*', 'No folder is selected', 1, True)
            skip = inputs.addBoolValueInput('skip', 'Skip identical snapshots?', True, '')
            skip.tooltip = "Skip the steps when the following operations: \nSketch/ConstructionPlane/ConstructionPoint/ConstructionAxis\n/ThreadFeature'/Combine'/Occurrence are performed, \nsince they make no visible changes to the model."
            text = inputs.addBoolValueInput('text', 'Add operation description?', True, '')
            text.tooltip = "Add operation description text on each frame"
            grid = inputs.addBoolValueInput('grid', 'Remove grids?', True, '')
            camera_view = inputs.addDropDownCommandInput('camera_view','Camera view',adsk.core.DropDownStyles.TextListDropDownStyle)
            views = camera_view.listItems
            views.add('Initial View', True, '')
            views.add('Front View', False, '')
            views.add('Top View', False, '')
            views.add('Right View', False, '')
            views.add('Left View', False, '')
            views.add('Back View', False, '')
           
        # Define inputs for MacOS
        elif operatingPlatform == "MacOS":
            imagename = inputs.addStringValueInput('imagename', 'Name*')
            selectFolderBtn = inputs.addBoolValueInput('selectFolderBtn', 'Select folder*', False, './Resources/button', False)
            targetFolder = inputs.addTextBoxCommandInput('targetFolder', 'Save directory*', 'No folder is selected', 1, True)
            skip = inputs.addBoolValueInput('skip', 'Skip identical snapshots?', True, '')
            skip.tooltip = "Skip the steps when the following operations: \nSketch/ConstructionPlane/ConstructionPoint/ConstructionAxis\n/ThreadFeature'/Combine'/Occurrence are performed, \nsince they make no visible changes to the model."
            grid = inputs.addBoolValueInput('grid', 'Remove grids?', True, '')
            camera_view = inputs.addDropDownCommandInput('camera_view','Camera view',adsk.core.DropDownStyles.TextListDropDownStyle)
            views = camera_view.listItems
            views.add('Initial View', True, '')
            views.add('Front View', False, '')
            views.add('Top View', False, '')
            views.add('Right View', False, '')
            views.add('Left View', False, '')
            views.add('Back View', False, '')

        # End the add-in when the OS is not supporting
        else:
            return

        # Connect to the commandDestroyed event.
        onDestroy = CommandDestroyHandler()
        cmd.destroy.add(onDestroy)
        handlers.append(onDestroy)
        
        # Connect to the inputChanged event
        onInputChanged = CommandInputChangedHandler()
        cmd.inputChanged.add(onInputChanged)
        handlers.append(onInputChanged)

        # Connect to the ValidateInputsHandler
        onValidateInputs = ValidateInputsHandler()
        cmd.validateInputs.add(onValidateInputs)
        handlers.append(onValidateInputs)

        # Connect to the execute event
        onExecute = CommandExecuteHandler()
        cmd.execute.add(onExecute)
        handlers.append(onExecute)

        
# Event handler for the commandDestroyed event
class CommandDestroyHandler(adsk.core.CommandEventHandler):
    def _init_(self):
        super()._init_()
    def notify(self, args):

        setGridDisplay(True)


# Event handler for the inputChanged event
class CommandInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args: adsk.core.ValidateInputsEventArgs):
        eventArgs = adsk.core.InputChangedEventArgs.cast(args)
        
        # Get the changed input
        changedInput = eventArgs.input
        inputs = eventArgs.firingEvent.sender.commandInputs
    
        # Check if select folder button is clicked
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

        # Check if remove grids is selected
        if changedInput.id == 'grid':
            if isGridDisplayOn ():
                setGridDisplay (False)
            else:
                setGridDisplay (True)

        # Check if camera view is changed
        if changedInput.id == 'camera_view':
            cameraView = changedInput.selectedItem.name
            camera = app.activeViewport.camera
            if(cameraView == 'Initial View'):
                camera = currentCamera
            elif(cameraView == 'Top View'):
                camera.viewOrientation = adsk.core.ViewOrientations.TopViewOrientation
            elif(cameraView == 'Front View'):
                camera.viewOrientation = adsk.core.ViewOrientations.FrontViewOrientation
            elif(cameraView == 'Left View'):
                camera.viewOrientation = adsk.core.ViewOrientations.LeftViewOrientation
            elif(cameraView == 'Right View'):
                camera.viewOrientation = adsk.core.ViewOrientations.RightViewOrientation
            elif(cameraView == 'Back View'):
                camera.viewOrientation = adsk.core.ViewOrientations.BackViewOrientation
            camera.isFitView = True
            app.activeViewport.camera = camera


class ValidateInputsHandler(adsk.core.ValidateInputsEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args: adsk.core.ValidateInputsEventArgs):
        
        eventArgs = adsk.core.ValidateInputsEventArgs.cast(args)

        if operatingPlatform == "Windows":
            filename = eventArgs.inputs.itemById("videoname")
        if operatingPlatform == "MacOS":
            filename = eventArgs.inputs.itemById("imagename")
        if not filename:
            return
        filepath = eventArgs.inputs.itemById("targetFolder")
        if not filepath:
            return

        if (filename.value and filepath.text != "No folder is selected"):
            # OK button enabled
            eventArgs.areInputsValid = True
        else:
            # OK button disabled
            eventArgs.areInputsValid = False


# Event handler for the execute event
class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        eventArgs = adsk.core.CommandEventArgs.cast(args)
   
        # Get the user inputs
        inputs = eventArgs.command.commandInputs

        # Take snapshots and convert into video for Windows
        if operatingPlatform == "Windows":
            videoname = inputs.itemById('videoname').value
            targetFolder = inputs.itemById('targetFolder').text
            skip = inputs.itemById('skip').value
            text = inputs.itemById('text').value
            
            # Save image
            count = timeline_var.count + 1 
            timeline_var.moveToBeginning()
            imageCount = 0

            for index in range(1, count) :
                # Take screenshot of timeline step and save it in specified path
                frame = "frame%s" % index
                filename = os.path.join(targetFolder, frame)
                filenames.append("%s.png" % filename)   
                entity = timeline_var.item(index-1).entity        
                timeline_step = type(entity).__name__
                if skip == True:
                    if timeline_step == 'Sketch' or timeline_step == 'ConstructionPlane' or timeline_step == 'ConstructionPoint' or timeline_step == 'ConstructionAxis' or timeline_step == 'ThreadFeature' or timeline_step == 'Combine' or timeline_step=='Occurrence':
                        returnValue = timeline_var.movetoNextStep()
                        continue
                size = saveImageForWindows(entity,targetFolder,timeline_step,frame,filename,text)   
                imageCount =+ 1 

            if imageCount == 0:
                ui.messageBox("All steps in timeline are skipped. No snapshot is taken.")

        
            import cv2

            # Create video and save in target folder
            name = targetFolder+'/'+videoname+'.mp4'
            out = cv2.VideoWriter(name,cv2.VideoWriter_fourcc(*'DIVX'), 1, size)
            for i in range(len(img_array)):
                out.write(img_array[i])
            out.release()

            # Display finish message
            ui.messageBox('Process video '+videoname+'.mp4 is saved to [' + targetFolder + '].')

            play_video = ui.messageBox('Play the video ?', '', 3, 1)

            # Display video
            if(play_video == 2) :
                from os import startfile
                startfile(name)
            
        # Take snapshots only for MacOS
        if operatingPlatform == "MacOS":
            filename = inputs.itemById('imagename').value
            targetFolder = inputs.itemById('targetFolder').text
            skip = inputs.itemById('skip').value

            count = timeline_var.count
            imageCount = 0
            timeline_var.moveToBeginning()

            for index in range(1, count+1) :
                # Take screenshot of timeline step and save it in specified path
                finalFilename = os.path.join(targetFolder, filename+"%s" % (imageCount+1))
                filenames.append("%s.png" % finalFilename)
                entity = timeline_var.item(index-1).entity        
                timeline_step = type(entity).__name__
                if skip == True:
                    if timeline_step == 'Sketch' or timeline_step == 'ConstructionPlane' or timeline_step == 'ConstructionPoint' or timeline_step == 'ConstructionAxis' or timeline_step == 'ThreadFeature' or timeline_step == 'Combine' or timeline_step=='Occurrence':
                        returnValue = timeline_var.movetoNextStep()
                        continue
                saveImgForMac(finalFilename, targetFolder)
                imageCount += 1

            # Display finish message
            if imageCount != 0:
                ui.messageBox(str(imageCount) + ' snapshots out of ' + str(timeline_var.count) + ' steps are saved to [' + targetFolder + '].')
                
                open_folder = ui.messageBox('Open the folder ?', '', 3, 1)
                # Open the folder
                if(open_folder == 2) :
                    import webbrowser
                    webbrowser.open('file:///' + targetFolder)
            else:
                ui.messageBox("All steps in timeline are skipped. No snapshot is taken.")

        setGridDisplay(True)

######################################## FUSION EVENT HANDLERS ########################################


################################### SELF-DEFINED HELIPING FUNCTIONS ###################################

def isGridDisplayOn ():
    app = adsk.core.Application.get ()
    ui = app.userInterface

    cmdDef = ui.commandDefinitions.itemById ('ViewLayoutGridCommand')
    listCntrlDef = adsk.core.ListControlDefinition.cast (cmdDef.controlDefinition)
    layoutGridItem = listCntrlDef.listItems.item (0)
    
    print('isGridDisplayOn', layoutGridItem.isSelected)

    if layoutGridItem.isSelected:
        return True
    else:
        return False
    

def setGridDisplay (turnOn):
    app = adsk.core.Application.get ()
    ui = app.userInterface

    cmdDef = ui.commandDefinitions.itemById ('ViewLayoutGridCommand')
    listCntrlDef = adsk.core.ListControlDefinition.cast (cmdDef.controlDefinition)
    layoutGridItem = listCntrlDef.listItems.item (0)
    
    if turnOn:
        layoutGridItem.isSelected = True
    else:
        layoutGridItem.isSelected = False   


def saveImageForWindows(entity,targetFolder,timeline_step,frame,filename,text):
    timeline_names.append(timeline_step)
    timeline_operation = getOperations(entity)
    operations.append(timeline_operation)

    returnValue = timeline_var.movetoNextStep()
    app.activeViewport.saveAsImageFile(filename, 0, 0)  

    import cv2

    # Add timeline step text to image
    path = '%s' % targetFolder+'/%s' % frame+'.png'
    img = cv2.imread(path)      
    font = cv2.FONT_HERSHEY_SIMPLEX
    if(text == True):
        cv2.putText(img, '%s' % timeline_step, (10,400), font, 3, (0, 0, 0), 2, cv2.LINE_AA) 
        cv2.putText(img, '%s' % timeline_operation, (10,450), font, 2, (0, 0, 0), 2, cv2.LINE_AA) 
    cv2.imwrite(path, img)
    height, width, layers = img.shape
    size = (width,height)
    img_array.append(img)

    return size


def saveImgForMac(filename, targetFolder):
    # Save image
    returnValue = timeline_var.movetoNextStep()
    app.activeViewport.saveAsImageFile(filename, 0, 0)  


def getPlatform():
    # Check OS
    from sys import platform
    if platform == "linux" or platform == "linux2":
        ui.messageBox('Sorry this add-in does not support Linux system.')
        return "Linux"
    elif platform == "darwin":
        msg = '<span>Only capturing timetine objects to snapshots is supported on MacOS.<br>For details please check our user manual at </span><a href="https://git.rwth-aachen.de/wingyin97606/mcp-group3">https://git.rwth-aachen.de/wingyin97606/mcp-group3</a><span>.</span>'
        ui.messageBox(msg, "Limited features on MacOS", 0, 2)
        return "MacOS"
    elif platform == "win32":
        return "Windows"
    ui.messageBox("Sorry this add-in does not support your operating system.")
    return "error"


# Get operation description of each step in timeline
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

################################### SELF-DEFINED HELIPING FUNCTIONS ###################################
    

def stop(context):
    try:
        # Delete button and command definition from ProcessCapturerPanel
        pcPanel = ui.allToolbarPanels.itemById('ProcessCapturerPanel')
        addInsButton = pcPanel.controls.itemById('processCapturerAddIn')       
        if addInsButton:
            addInsButton.deleteMe()
        cmdDef = ui.commandDefinitions.itemById('processCapturerAddIn')
        if cmdDef:
            cmdDef.deleteMe()

        # Delete button and command definition from SolidScriptsAddinsPanel
        scPanel = ui.allToolbarPanels.itemById('SolidScriptsAddinsPanel')
        addInsButton = scPanel.controls.itemById('processCapturerAddIn')       
        if addInsButton:
            addInsButton.deleteMe()
        cmdDef = ui.commandDefinitions.itemById('processCapturerAddIn')
        if cmdDef:
            cmdDef.deleteMe()

        ui.messageBox('ProcessCapturer has been stopped. Thank you for using!')

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
