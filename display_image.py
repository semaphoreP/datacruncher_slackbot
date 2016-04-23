import os
import matplotlib
import matplotlib.pylab as plt
import astropy.io.fits as fits
import numpy as np

def get_title_from_filename(filename):
    """
    Generate title by parsing filename
    
    Args:
        filename: pull path to file
    Return:
        title: title to plot
    """
    filepath_args = filename.split(os.path.sep)
    objname = filepath_args[-4]
    objname = objname.replace("_", " ")
    dateband = filepath_args[-2].split("_")
    date = dateband[0]
    date = "{0}-{1}-{2}".format(date[0:4], date[4:6], date[6:8])
    band = dateband[1]
    mode = dateband[2]

    title = "{obj} {date} {band}-{mode}".format(obj=objname, date=date, band=band, mode=mode)
    return title


def save_klcube_image(filename, outputname, title=None):
    """
    Open the PSF Subtraction saved as a KL Mode Cube and write the image as a PNG
    in the path as specified by outputname
    
    Args:
        filename: path to KL Mode cube to display
        outputname: output PNG filepath
        title: title of saved PNG plot
        
    Return:
        None
    """
    hdulist = fits.open(filename)
    klcube = hdulist[1].data
    frame50 = klcube[3]
    hdulist.close()
    
    # rough throuhghput calibration
    if 'methane' in filename:
        throughput_corr = 1.1
    else:
        throughput_corr = 0.65
    frame50 /= throughput_corr
    
    # make strictly positive for log stretch
    minval = np.nanmin(frame50) - 1
    log_frame = np.log(frame50 - minval)
       
    limits = [-3.e-7, np.min([np.nanpercentile(frame50, 99.6), 8.e-5])]
    
    # set colormap to have nans as black
    cmap = matplotlib.cm.viridis
    cmap.set_bad('k',1.)
    
    # plot
    fig = plt.figure()
    ax = fig.add_subplot(111)
    im = ax.imshow(log_frame, cmap=cmap, vmin=np.log(limits[0]-minval), vmax=np.log(limits[1]-minval))
    ax.invert_yaxis()

    
    #add colorbar
    cbar = plt.colorbar(im, orientation='vertical', shrink=0.9, pad=0.015, ticks=[np.log(limits[0]-minval),np.log(-minval), (np.log(limits[0]-minval)*2 + np.log(limits[1]-minval))/3., (np.log(limits[0]-minval) + np.log(limits[1]-minval)*2)/3. ,np.log(limits[1]-minval)])
    cbar.ax.set_yticklabels(["{0:.1e}".format(limits[0]), "0", "{0:.1e}".format((np.exp((np.log(limits[0]-minval)*2 + np.log(limits[1]-minval))/3))+minval), "{0:.1e}".format((np.exp((np.log(limits[0]-minval) + np.log(limits[1]-minval)*2)/3))+minval), "{0:.1e}".format(limits[1])])
    cbar.set_label("Contrast", fontsize=12)
    cbar.ax.tick_params(labelsize=12) 
    
    ax.set_title(title)
    
    plt.savefig(outputname)
    
    
# For testing purposes only
if __name__ == "__main__":
    save_klcube_image('C:\\Users\\jwang\\OneDrive\\GPI\\data\\Reduced\\hd95086\\pyklip-S20160229-H-k150a9s4m1-KLmodes-all.fits', "tmp.png", "HD 95086 2016-02-29 H-Spec")
