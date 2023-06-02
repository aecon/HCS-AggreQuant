import os
import sys
import numpy as np
import argparse
import skimage.io
import skimage.filters
import skimage.morphology
from skimage import restoration
import matplotlib.pyplot as plt
from scipy import ndimage
from skimage.segmentation import watershed

from filenames import Filenames
from diagnostics import Diagnostics



def scale_values_01_float(img):
    """
    Return image with values scaled between 0 and 1
    """
    IMIN = np.min(img)
    IMAX = np.max(img)

    img1 = (img-IMIN)/(IMAX-IMIN)
    img2 = np.asarray(img1, dtype=float)

    scale = np.asarray([IMIN, IMAX])

    return img2, scale


def segment_cellpose():
    print("TODO")
    assert(0)
    nuclei_paths = ""
    for f in images_nuclei:
        nuclei_paths+=" '%s'" % f
    os.system( "conda run -n cellpose python cells_cp.py -o %s -i %s" % (Names.OUTDIR, nuclei_paths) ) ### CHECK THE PATHS !!!!


def segment_distance_map(image_file, seeds_file, allnuclei_file, opath, Names):

    # TODO:
    # > compute average intensity of image. Proceed based on average intensity ..

    bpath = os.path.basename(image_file)


    # load image and convert to float
    img0 = skimage.io.imread(image_file, plugin='tifffile')
    img0 = np.asfarray(img0, float)

    # 1. GENERATE MASK OF CELLBODY AREA
    # background division
    smt = skimage.filters.gaussian(img0, sigma=2)
    #print("Smooth s=2:", np.min(smt), np.max(smt))
    img_cap = np.zeros(np.shape(img0))
    img_cap[:,:] = img0[:,:]
    img_cap[img0>1000] = 1000
    bkg = skimage.filters.gaussian(img_cap, sigma=50)
    #print("Smooth s=50, capped:", np.min(bkg), np.max(bkg))
    img1 = smt / bkg

    #print("After BEQ:", np.min(img1), np.max(img1))
    img11, scale = scale_values_01_float(img1)
    #print("After scaling 0/1 (float):", np.min(img11), np.max(img11))
    img2 = skimage.exposure.equalize_adapthist(img11, kernel_size=150)
    #print("After CLAHE:", np.min(img2), np.max(img2))

    IMIN = scale[0]
    IMAX = scale[1]
    cells_area = img2*(IMAX-IMIN)+IMIN

    cell_mask_ = np.zeros(np.shape(cells_area), dtype=np.dtype(np.uint8))
    cell_mask_[cells_area>1.5] = 1
    #plt.imshow(cell_mask_)
    #plt.show()

    # remove small holes
    cell_mask = skimage.morphology.remove_small_holes(cell_mask_, area_threshold=400)
    #plt.imshow(cell_mask)
    #plt.show()

    # 2. SPLIT CELL MASK BASED on NUCLEI SEEDS

    # load image and convert to float
    allnuclei = skimage.io.imread(allnuclei_file, plugin='tifffile')
    allnuclei_mask = np.zeros(np.shape(allnuclei), dtype=np.dtype(np.uint8))
    allnuclei_mask[allnuclei>0] = 1

    # load image and convert to float
    seeds = skimage.io.imread(seeds_file, plugin='tifffile')  # uint8

    # compute distances to all nuclei
    distances = ndimage.distance_transform_edt(1-allnuclei_mask)  # float64
    #plt.imshow(distances)
    #plt.show()

    # watershed of distance map
    labels_ = watershed(distances, mask=cell_mask, watershed_line=True)
    labels = np.zeros(np.shape(allnuclei_mask), dtype=np.dtype(np.uint16))
    labels[labels_>0] = labels_[labels_>0]
    #plt.imshow(labels)
    #plt.show()

    # Remove cellbodies that do not contain nucleus
    AllLabels = np.unique(labels[labels>0])
    for l in AllLabels:
        idx = labels==l
        is_seed = np.sum(seeds[idx])
        if is_seed < 100:
            labels[idx] = 0
            print("No seed for label", l)
    #plt.imshow(labels)
    #plt.show()
    skimage.io.imsave("%s/%s_cellbodies_labels.tif" % (opath, bpath), labels, plugin='tifffile')

    # Assign a cell area to each nucleus
    nuclei_labels = np.zeros(np.shape(labels), dtype=np.dtype(np.uint16))
    nuclei_labels[labels>0] = labels[labels>0]
    nuclei_labels[seeds==0] = 0
    #plt.imshow(nuclei_labels)
    #plt.show()
    skimage.io.imsave("%s/%s_corresponding_nuclei.tif" % (opath, bpath), nuclei_labels, plugin='tifffile')

    # find edges
    nuclei_labels[nuclei_labels>0] = 1
    edges0 = skimage.filters.sobel(nuclei_labels)
    edges = np.zeros(np.shape(edges0), dtype=np.dtype(np.uint8))
    edges[edges0>0] = 1
    fat_edges = edges #skimage.morphology.binary_dilation(edges)

    # overlay cells and nuclei edges
    composite = np.zeros( np.shape(labels), dtype=np.dtype(np.uint16) )
    composite[:,:] = labels[:,:]
    composite[fat_edges==1] = 0
    skimage.io.imsave("%s/%s_%s.tif" % (opath, bpath, Names.COMPOSITE_CELLS_AND_NUCLEI ), composite, plugin='tifffile')



def segment_intensity_map(image_file, seeds_file, allnuclei_file, opath, Names):

    # TODO:
    # > compute average intensity of image. Proceed based on average intensity ..

    bpath = os.path.basename(image_file)

    # load image and convert to float
    img0 = skimage.io.imread(image_file, plugin='tifffile')
    img0 = np.asfarray(img0, float)

    # 1. GENERATE MASK OF CELLBODY AREA
    # background division
    smt = skimage.filters.gaussian(img0, sigma=2)
    #print("Smooth s=2:", np.min(smt), np.max(smt))
    img_cap = np.zeros(np.shape(img0))
    img_cap[:,:] = img0[:,:]
    img_cap[img0>1000] = 1000
    bkg = skimage.filters.gaussian(img_cap, sigma=50)
    #print("Smooth s=50, capped:", np.min(bkg), np.max(bkg))
    img1 = smt / bkg

    #print("After BEQ:", np.min(img1), np.max(img1))
    img11, scale = scale_values_01_float(img1)
    #print("After scaling 0/1 (float):", np.min(img11), np.max(img11))
    img2 = skimage.exposure.equalize_adapthist(img11, kernel_size=150)
    #print("After CLAHE:", np.min(img2), np.max(img2))

    IMIN = scale[0]
    IMAX = scale[1]
    cells_area = img2*(IMAX-IMIN)+IMIN

    cell_mask_ = np.zeros(np.shape(cells_area), dtype=np.dtype(np.uint8))
    cell_mask_[cells_area>1.5] = 1
    #plt.imshow(cell_mask_)
    #plt.show()

    # remove small holes
    cell_mask = skimage.morphology.remove_small_holes(cell_mask_, area_threshold=400)
    #plt.imshow(cell_mask)
    #plt.show()

    # 2. SPLIT CELL MASK BASED on NUCLEI SEEDS

    # load image and convert to float
    allnuclei = skimage.io.imread(allnuclei_file, plugin='tifffile')
    allnuclei_mask = np.zeros(np.shape(allnuclei), dtype=np.dtype(np.uint8))
    allnuclei_mask[allnuclei>0] = 1

    # load image and convert to float
    seeds = skimage.io.imread(seeds_file, plugin='tifffile')  # uint8

    # field to use for watershed
    intensity_field_ = skimage.filters.gaussian(img2, sigma=6)
    intensity_field, _ = scale_values_01_float(intensity_field_)
    field = 1.0 - intensity_field
    field[allnuclei_mask==1] = 0
    #print(np.min(field), np.max(field))
    #plt.imshow(field)
    #plt.show()

    # compute distances to all nuclei
    #distances = ndimage.distance_transform_edt(1-allnuclei_mask)  # float64
    #plt.imshow(distances)
    #plt.show()

    # watershed of distance map
    labels_ = watershed(field, mask=cell_mask, watershed_line=True)
    labels = np.zeros(np.shape(allnuclei_mask), dtype=np.dtype(np.uint16))
    labels[labels_>0] = labels_[labels_>0]
    #plt.imshow(labels)
    #plt.show()

    # Remove cellbodies that do not contain nucleus
    AllLabels = np.unique(labels[labels>0])
    for l in AllLabels:
        idx = labels==l
        is_seed = np.sum(seeds[idx])
        if is_seed < 100:
            labels[idx] = 0
            print("No seed for label", l)
    #plt.imshow(labels)
    #plt.show()
    skimage.io.imsave("%s/%s_cellbodies_labels.tif" % (opath, bpath), labels, plugin='tifffile')

    # Assign a cell area to each nucleus
    nuclei_labels = np.zeros(np.shape(labels), dtype=np.dtype(np.uint16))
    nuclei_labels[labels>0] = labels[labels>0]
    nuclei_labels[seeds==0] = 0
    #plt.imshow(nuclei_labels)
    #plt.show()
    skimage.io.imsave("%s/%s_corresponding_nuclei.tif" % (opath, bpath), nuclei_labels, plugin='tifffile')

    # find edges
    nuclei_labels[nuclei_labels>0] = 1
    edges0 = skimage.filters.sobel(nuclei_labels)
    edges = np.zeros(np.shape(edges0), dtype=np.dtype(np.uint8))
    edges[edges0>0] = 1
    fat_edges = edges #skimage.morphology.binary_dilation(edges)

    # overlay cells and nuclei edges
    composite = np.zeros( np.shape(labels), dtype=np.dtype(np.uint16) )
    composite[:,:] = labels[:,:]
    composite[fat_edges==1] = 0
    skimage.io.imsave("%s/%s_%s.tif" % (opath, bpath, Names.COMPOSITE_CELLS_AND_NUCLEI ), composite, plugin='tifffile')



def segment_propagation():
    print("TODO")


def cellbody_segmentation(cellbody_images, Names):


    segmentation_algorithm = Names.CELLBODY_SEGMENTATION_TYPE
    print("Segmenting cell bodies with algorithm:", segmentation_algorithm)

    for ifile, image_file in enumerate(cellbody_images):

        bpath = os.path.basename(image_file)
        print(">> Processing image: %s" % bpath)

        # find corresponding nuclei seeds
        allnuclei_file = "%s/%s/nuclei/%s%s).tif_labels_StarDist.tif" % (Names.OUTDIR_PATH, Names.OUTDIR, bpath.split(Names.COLOR_CELLS,1)[0], Names.COLOR_NUCLEI)
        seeds_file = "%s/%s/nuclei/%s%s).tif_seeds_nuclei.tif" % (Names.OUTDIR_PATH, Names.OUTDIR, bpath.split(Names.COLOR_CELLS,1)[0], Names.COLOR_NUCLEI)
        if not os.path.isfile(seeds_file):
            print("Nuclei Seeds for file %s do NOT exist!", bpath)
            sys.exit()

        # Choose segmentation algorithm for cellbodies
        if segmentation_algorithm == "distance":
            opath = "%s/%s/cellbodies_distance" % ( Names.OUTDIR_PATH, Names.OUTDIR)
            if not os.path.exists(opath):
                print("Path %s does NOT exist. Creating now. " % opath)
                os.makedirs(opath)
            else:
                print("Path %s exists." % opath)
            segment_distance_map(image_file, seeds_file, allnuclei_file, opath, Names)

        elif segmentation_algorithm == "intensity":
            opath = "%s/%s/cellbodies_intensity" % ( Names.OUTDIR_PATH, Names.OUTDIR)
            if not os.path.exists(opath):
                print("Path %s does NOT exist. Creating now. " % opath)
                os.makedirs(opath)
            else:
                print("Path %s exists." % opath)
            segment_intensity_map(image_file, seeds_file, allnuclei_file, opath, Names)

        elif segmentation_algorithm == "propagation":
            segment_propagation()
        elif segmentation_algorithm == "cellpose":
            segment_cellpose()
        else:
            print("Segmentation algorithm %s not defined." % segmentation_algorithm)
            sys.exit()


        #assert(0)


