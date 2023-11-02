import pigeon

import os
os.chdir(os.path.dirname(__file__))

print(os.path.abspath(os.curdir))
print("\n".join(sorted(os.listdir(os.curdir + "/data"))))

pigeon.main()
