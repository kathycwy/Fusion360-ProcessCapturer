#Author-Wingyin Chan, Sai Limaye
#Description-Convert your creation process into images/video

import adsk.core, adsk.fusion, adsk.cam, traceback
import os,sys
import time
import json

#get the path of add-in
my_addin_path = os.path.dirname(os.path.realpath(__file__)) 

#add the path to the searchable path collection
if not my_addin_path in sys.path:
    sys.path.append(my_addin_path) 

# Global list to keep all event handlers in scope
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
  
        workSpace = ui.workspaces.itemById('FusionSolidEnvironment')
        tbPanels = workSpace.toolbarPanels

        global tbPanel
        pcPanel = tbPanels.itemById('ProcessCapturerPanel')
        if pcPanel:
            pcPanel.deleteMe()
        pcPanel = tbPanels.add('ProcessCapturerPanel', 'Process Capturer', 'SelectPanel', False)

        # Get the CommandDefinitions collection
        cmdDefs = ui.commandDefinitions
        
        # Create a command definition and add a button to the Add-ins panel.
        cmdDef = ui.commandDefinitions.addButtonDefinition('processCapturerAddIn', 
                                                            'Process Capturer', 
                                                            'Convert your creation process into images/video',
                                                            './Resources')        
        # Add button to new ProcessCapturerPanel
        pcPanel = ui.allToolbarPanels.itemById('ProcessCapturerPanel')
        addInsButton = pcPanel.controls.addCommand(cmdDef)
        # Add button to original SolidScriptsAddinsPanel
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
    
        global operatingPlatform 
        operatingPlatform = getPlatform()
      
        #Define inputs for Windows
        if operatingPlatform == "Windows":
            filename = inputs.addStringValueInput('videoname', 'Video name')
            targetFolder = inputs.addTextBoxCommandInput('targetFolder', 'Save directory', '', 1, False)
            selectFolderBtn = inputs.addBoolValueInput('selectFolderBtn', 'Select', False, '', False)
            # rotate = inputs.addBoolValueInput('rotate', 'Rotate Design?', True, '')
            skip = inputs.addBoolValueInput('skip', 'Skip non-visible steps?', True, '')
            grid = inputs.addBoolValueInput('grid', 'Remove/Add grid?', True, '')
            camera_view = inputs.addDropDownCommandInput('camera_view','Camera view',adsk.core.DropDownStyles.TextListDropDownStyle)
            views = camera_view.listItems
            views.add('Current View', True, '')
            views.add('Front View', False, '')
            views.add('Top View', False, '')
            views.add('Right View', False, '')
            views.add('Left View', False, '')
            views.add('Back View', False, '')
            # background = inputs.addBoolValueInput('background', 'Add background?', True, '')
            # range_start = inputs.addTextBoxCommandInput('range_start', 'Range start', '', 1, False)
            # range_end = inputs.addTextBoxCommandInput('range_end', 'Range end', '', 1, False)


        #Define inputs for MacOS
        if operatingPlatform == "MacOS":
            filename = inputs.addStringValueInput('imagename', 'Image name')
            htmlBtn = inputs.addBrowserCommandInput('htmlBtn', 'Save directory', './Resources/selectPathBrowserInput.html', 28, 28)
            targetFolder = inputs.addTextBoxCommandInput('targetFolder', 'Save directory', '', 1, False)
            selectFolderBtn = inputs.addBoolValueInput('selectFolderBtn', 'Select', False, '', False)
            skip = inputs.addBoolValueInput('skip', 'Skip non-visible steps?', True, '')
            grid = inputs.addBoolValueInput('grid', 'Remove/Add grid?', True, '')
            camera_view = inputs.addDropDownCommandInput('camera_view','Camera view',adsk.core.DropDownStyles.TextListDropDownStyle)
            views = camera_view.listItems
            views.add('Current View', True, '')
            views.add('Front View', False, '')
            views.add('Top View', False, '')
            views.add('Right View', False, '')
            views.add('Left View', False, '')
            views.add('Back View', False, '')

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

        if changedInput.id == 'grid':
            if isGridDisplayOn ():
                setGridDisplay (False)
            else:
                setGridDisplay (True)


        if changedInput.id == 'camera_view':
            cameraView = changedInput.selectedItem.name
            camera = app.activeViewport.camera
            if(cameraView == 'Top View'):
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


# Event handler for the execute event
class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        eventArgs = adsk.core.CommandEventArgs.cast(args)
   
        # Get the user inputs
        inputs = eventArgs.command.commandInputs
        

        if operatingPlatform == "Windows":
            videoname = inputs.itemById('videoname').value
            targetFolder = inputs.itemById('targetFolder').text
            #rotate = inputs.itemById('rotate').value
            skip = inputs.itemById('skip').value
            # background = inputs.itemById('background').value
            # start = inputs.itemById('range').valueOne
            # end = inputs.itemById('range').valueTwo
            
            #Save image
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
                    if skip == True:
                        continue
                    else:
                        size = saveImageForWindows(entity,targetFolder,timeline_step,frame,filename) 
                else:
                    size = saveImageForWindows(entity,targetFolder,timeline_step,frame,filename)    
        
            import cv2

            #Create video and save in target folder
            name = targetFolder+'/'+videoname+'.mp4'
            out = cv2.VideoWriter(name,cv2.VideoWriter_fourcc(*'DIVX'), 1, size)
            for i in range(len(img_array)):
                out.write(img_array[i])
            out.release()

            play_video = ui.messageBox('Play the video ?', 'This is a message box', 3, 1)
            #Display video
            if(play_video == 2) :
                cap = cv2.VideoCapture(name)
                fps= int(cap.get(cv2.CAP_PROP_FPS))
                while(True):
                    ret, frame = cap.read()
                    time.sleep(1/fps)
                    cv2.imshow('Frame', frame)
                    if cv2.waitKey(25) & 0xFF == ord('q'):
                        break  
                cap.release()
                cv2.destroyAllWindows()
            else :
                # Display finish message
                ui.messageBox(str(timeline_var.count) + ' snapshots are taken.\nProcess video '+videoname+'.mp4 is saved to [' + targetFolder + '].')

          
        if operatingPlatform == "MacOS":
            imagename = inputs.itemById('imagename').value
            targetFolder = inputs.itemById('targetFolder').text
            skip = inputs.itemById('skip').value

            count = timeline_var.count
            timeline_var.moveToBeginning()

            for index in range(1, count+1) :
                #Take screenshot of timeline step and save it in specified path
                filename = os.path.join(targetFolder, imagename+"%s" % index)
                filenames.append("%s.png" % filename)
                entity = timeline_var.item(index-1).entity        
                timeline_step = type(entity).__name__
                if skip == True:
                    if timeline_step == 'Sketch' or timeline_step == 'ConstructionPlane' or timeline_step == 'ConstructionPoint' or timeline_step == 'ConstructionAxis' or timeline_step == 'ThreadFeature' or timeline_step == 'Combine' or timeline_step=='Occurrence':
                        returnValue = timeline_var.movetoNextStep()
                        continue
                saveImgForMac(filename, targetFolder)

            # Display finish message
            ui.messageBox(str(timeline_var.count) + ' snapshots are saved to [' + targetFolder + '].')


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


def saveImageForWindows(entity,targetFolder,timeline_step,frame,filename):
    timeline_names.append(timeline_step)
    timeline_operation = getOperations(entity)
    operations.append(timeline_operation)

    returnValue = timeline_var.movetoNextStep()
    app.activeViewport.saveAsImageFile(filename, 0, 0)  

    import cv2

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


def saveImgForMac(filename, targetFolder):
    # Save image
    returnValue = timeline_var.movetoNextStep()
    app.activeViewport.saveAsImageFile(filename, 0, 0)  



def getPlatform():
    #Check OS
    from sys import platform
    if platform == "linux" or platform == "linux2":
        ui.messageBox('Sorry this add-in does not support Linux system.')
        return "Linux"
    elif platform == "darwin":
        ui.messageBox("Only capturing timetine objects to snapshots is supported on MacOS.\nFor details please check our user manual at https://git.rwth-aachen.de/wingyin97606/mcp-group3.", "Limited features on MacOS", 0, 2)
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
        addInsPanel = ui.allToolbarPanels.itemById('ProcessCapturerPanel')
        addInsButton = addInsPanel.controls.itemById('processCapturerAddIn')       
        if addInsButton:
            addInsButton.deleteMe()
        
        cmdDef = ui.commandDefinitions.itemById('processCapturerAddIn')
        if cmdDef:
            cmdDef.deleteMe()
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
