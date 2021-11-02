
#Authors - Wing Yin Chan - Sai Limaye
#Description - MCP - A03 - Group 3

import adsk.core, adsk.fusion, adsk.cam, traceback
import math, random

def run(context):
    
    # ui = None
    app = adsk.core.Application.get()

    ui  = app.userInterface

    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)        
    design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))

    # Get a reference to an appearance in the library.
    lib = app.materialLibraries.itemByName('Fusion 360 Appearance Library')
    libAppear = lib.appearances.itemByName('Plastic - Matte (Yellow)')

    # Get the root component of the active design.	
    rootComp = design.rootComponent
    
    try:
        n = random.randint(5,10)
        for x in range(n):
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
            revInput = revolves.createInput(prof, axis, adsk.fusion.FeatureOperations.NewComponentFeatureOperation)

            # Define a revolve by specifying a specific revolve angle.
            angle = adsk.core.ValueInput.createByReal(math.pi * 2 * (x+1) / n)
            revInput.setAngleExtent(False, angle)
                    
            # Create the revolve by calling the add method on the RevolveFeatures collection and passing it the RevolveInput object.
            rev = revolves.add(revInput)

            comp = rev.parentComponent
            
            # Get the single occurrence that references the component.
            occs = rootComp.allOccurrencesByComponent(comp)
            occ = occs.item(0)
            
            # Create a copy of the existing appearance.
            newAppear = design.appearances.addByCopy(libAppear, 'Color ' + str(x+1))
            
            # Edit the "Color" property by setting it to a random color.
            colorProp = adsk.core.ColorProperty.cast(newAppear.appearanceProperties.itemByName('Color'))
            red = random.randint(0,255)
            green = random.randint(0,255)
            blue = random.randint(0,255)
            colorProp.value = adsk.core.Color.create(red, green, blue, 1)          
            
            # Assign the new color to the occurrence.
            occ.appearance = newAppear

            del newAppear

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
