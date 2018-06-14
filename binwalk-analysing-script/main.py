import sys
import os
import fnmatch
import binwalk

# If we have a basepath arg, good
# Otherwise bad
if len(sys.argv) > 2:
    print("You cannot pass more then one argument - the base path!")
    exit(1)

# Check if a basepath is provided, or we provide a default one
if len(sys.argv) == 2:
    basepath = sys.argv[1]
else:
    basepath = r'C:\Users\Andreea Gheorghe\PycharmProjects\axb1080\data-collection-script\downloads'

# Test the path for existence
try:
    if not os.path.exists(basepath):
        print("Base path does not exist!")
        exit(1)
except OSError as e:
    print("An OS error occurred - %s" % e)
    exit(1)
except Exception as e:
    print("A general exception occurred - %s" % e)
    exit(1)

# Binaries with signature paths will be hold here
binaries_with_signature = []
binaries_analysed = 0

try:
    # Get the binaries paths
    for root_path, dirnames, filenames in os.walk(basepath):
        for filename in fnmatch.filter(filenames, "*.bin"):
            # Go through all the binaries and analyse them one by one
            binary = os.path.join(root_path, filename)
            # Analyse each binary and log the output 1 at a time
            print("Analysing binary %s..." % binary)
            for binwalk_module in binwalk.scan("--log=%s.walkdat" % binary, "--verbose", binary, signature=True, quiet=True):
                binaries_analysed = binaries_analysed + 1
                if len(binwalk_module.results) > 0:
                    # If the binary has signatures, append it to the list
                    binaries_with_signature.append(binary)

except OSError as e:
    print("An OSError occurred - %s" % e)
except binwalk.ModuleException as e:
    print("A binwalk error courred - %s" % e)
except Exception as e:
    print("A general exception occurred - %s" % e)

print("Done")