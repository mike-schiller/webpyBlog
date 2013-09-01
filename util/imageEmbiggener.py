import sys
import Image

def interpolateImage(inputImageFileName,outputImageFileName):
  inputImage = Image.open(inputImageFileName)
  print inputImage.size
  if inputImage.size[0] >= 1118:
    print "no resize performed. image already at least 1118px wide"
    sys.exit(-2)
  else:
    newWidth = 1118
    heightMultiplier = float(newWidth)/float(inputImage.size[0])
    newHeight = int(heightMultiplier*inputImage.size[1])
    outputImage = inputImage.resize((newWidth,newHeight), Image.BICUBIC)
    outputImage.save(outputImageFileName) 

def usage():
  print 'python imageInterpolator.py inputImage outputImage'
  print "note, this scales images with widths smaller than"
  print "1118px to a width of 1118px while maintaining aspect"
  print "ratio. The blog template expects images roughly"
  print "1118px wide by 525px high"
  sys.exit(-1)

if __name__ == "__main__":
  if len(sys.argv) is not 3:
    usage()
  else:
    interpolateImage(sys.argv[1],sys.argv[2])
