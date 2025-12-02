# PC_Marketplace
URL: http://ec2-18-221-6-28.us-east-2.compute.amazonaws.com:8000/

This project uses BuildCores OpenDB


## Setup
### 1. Setup venv
python -m venv venv
**For windows call:** venv/Scripts/activate
**For linux call:** source venv/bin/activate
pip install -r requirements.txt

### 2. Setup DB
python manage.py migrate

### 3. Populate Product model
python manage.py shell


from products.utils import import_from_opendb
import_from_opendb("CPU") # NOTE: This is temp since eventually we will have more than the CPU model
exit()

