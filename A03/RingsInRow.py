#Author - Wing Yin Chan - Sai Limaye
#Description - MCP - A03 - Group3

import adsk.core, adsk.fusion, adsk.cam, traceback
import math, random

def createRing(x,n):
    
    app = adsk.core.Application.get()

    product = app.activeProduct
    rootComp = product.rootComponent

    ui  = app.userInterface

    design = adsk.fusion.Design.cast(app.activeProduct)

    # Get the root component of the active design.	
    rootComp = design.rootComponent

    # Create a new sketch on the xy plane.	
    sketches = rootComp.sketches
    xyPlane = rootComp.xYConstructionPlane
    sketch = sketches.add(xyPlane)

    # Create a new ObjectCollection.
    objColl = adsk.core.ObjectCollection.create()
    # Get the SketchCircles collection from an existing sketch.
    circles = sketch.sketchCurves.sketchCircles

    # Call an add method on the collection to create a new circle.
    circle1 = circles.addByCenterRadius(adsk.core.Point3D.create(x * 5,0,0), 2)

    # Get the SketchLines collection from an existing sketch.
    lines = sketch.sketchCurves.sketchLines

    # Call an add method on the collection to create a new line.
    axis = lines.addByTwoPoints(adsk.core.Point3D.create(-1,-4,0), adsk.core.Point3D.create(1,-4,0))

    # Get the first profile from the sketch, which will be the profile defined by the circle in this case.
    prof = sketch.profiles.item(0)

    # Get the RevolveFeatures collection.
    revolves = rootComp.features.revolveFeatures

    # Create a revolve input object that defines the input for a revolve feature.
    # When creating the input object, required settings are provided as arguments.
    revInput = revolves.createInput(prof, axis, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)

    # Define a full revolve by specifying 2 pi as the revolve angle.
    angle = adsk.core.ValueInput.createByReal(math.pi * 2 * (x+1) / n)
    revInput.setAngleExtent(False, angle)
            
    # Create the revolve by calling the add method on the RevolveFeatures collection and passing it the RevolveInput object.
    rev = revolves.add(revInput)

def run(context):
    
    ui = None
    
    try:
        n = random.randint(5,10)
        for x in range(n):
            createRing(x,n)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
