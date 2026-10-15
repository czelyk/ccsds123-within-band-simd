This documentation file was generated on 2024-07-16 by Sebastià Mijares i Verdú.



GENERAL INFORMATION
-------------------

1. Title of Dataset: 
Landsat 8 OLI (L1) 7-band 4096x4096 scenes from multiple locations around the world (Dataset)


2. Authorship: 

	Name: Mijares i Verdú, Sebastià
	Institution: Universitat Autònoma de Barcelona. Departament d'Enginyeria de la Informació i de les Comunicacions
	ORCID: 0000-0003-1038-6413

	
3. Contact:

	Name: Mijares i Verdú, Sebastià
	Institution: Universitat Autònoma de Barcelona. Departament d'Enginyeria de la Informació i de les Comunicacions
	E-mail: sebastia.mijares@uab.cat
	ORCID: 0000-0003-1038-6413



DESCRIPTION
-----------

1. Dataset language: 
English


2. Abstract:
Landsat 8 OLI (L1) 7-band 4096x4096 scenes from  multiple locations around the world.
This data set contains 21 L1-calibrated scenes from the OLI multispectral onboard the Landsat 8 NASA mission. All scenes are 7 bands (bands 1-7 from the OLI) and cropped to a standardised 4096x4096 size, stored as raw 16-bit unsigned integers, in little endian byte order and in band-sequential (BSQ) order. This data was collected over a varied range of locations around the world between 2013 and 2021 and were obtained from the Landsat 8 data repository in Google Cloud https://console.cloud.google.com/storage/browser/gcp-public-data-landsat/LC08/01?pageState=(%22StorageObjectListTable%22:(%22f%22:%22%255B%255D%22))&prefix=&forceOnObjectsSortingFiltering=false&rapt=AEjHL4Oce-7moqNK0g-5W2KKn-HKYkqfOXCTQ3ePOb3rAtTcz6OZt0TrkBXJA-CPjkXDIEyq94o6f5twpjgM_mqoYjzJcbewKXbFZsYnxXALXFVofiSO6gY. Specific dates and locations of each scene may be identified using the ID code in the scene name. These scenes compose a test set to evaluate compression algorithms for multispectral data.


3. Keywords:
Landsat 8
Operational Land Imager
OLI
Multispectral
Remote sensing


4. Kind of data:
Measurement and test data


5. Date of data collection (single date or date range):
2013-03-22 - 2021-08-15


6. Date of dataset publication:
2024-09-02


7. Funding sources: 

	Funding agency: AGAUR, Generalitat de Catalunya
	Project number: 2021/SGR-00643

	Funding agency: Agencia Estatal de Investigación
	Project number: PRE2019-088824

	Funding agency: Agencia Estatal de Investigación
	Project number: PID2021-125258OB-I00


8. Geographic location/s of data collection:
Miscellaneous.



ACCESS INFORMATION
------------------

1. Creative Commons License of the dataset:
CC0


2. Dataset DOI:
https://doi.org/10.34810/data1514


3. Related publication:
Mijares Verdú, S., Chabert, M., Oberlin, T., & Serra Sagrista, J. (2023). Reduced-Complexity Multirate Remote Sensing Data Compression With Neural Networks. IEEE Geoscience and Remote Sensing Letters, 20, Article 6011705. https://doi.org/10.1109/LGRS.2023.3325477


4. Link to related datasets:
	DOI/URL: https://github.com/smijares/mcos2023



VERSIONING AND PROVENANCE
-------------------------

1. Last modification date:
2023-02-16


2. Was data derived from another source?:
Yes. https://console.cloud.google.com/storage/browser/gcp-public-data-landsat/LC08/01;tab=objects?pageState=(%22StorageObjectListTable%22:(%22f%22:%22%255B%255D%22))&prefix=&forceOnObjectsSortingFiltering=false&pli=1&rapt=AEjHL4MI2qM0XJh7z9JaKp-2w50lKc__eBHK8IVEIdO4O4er6Snov1u-Sc1L8H7XyoQSoMfkW6UrevWRsSHYrJouaul4L5SK8OeqiO-232UxlsR10-vT-4Q


3. Additional related data collected that was not included in the current data package:
Landsat 8 OLI training data set.



METHODOLOGICAL INFORMATION
--------------------------

1. Description of methods used for collection-generation of data: 
OLI is a push-broom sensor with a four-mirror telescope and 12-bit quantization. OLI collects data for visible, near infrared, and short wave infrared spectral bands as well as a panchromatic band.


2. Methods for processing the data: 
The panchromatic band (8) and band 9 are discarded. No further preprocessing is done.


3. Instrument- or software- specific information needed to interpret the data:
None.


4. Instruments, calibration and standards information:
N/A


5. Environmental or experimental conditions:
N/A


6. Quality-assurance procedures performed on the data:
N/A



FILE OVERVIEW
--------------

1. Explain the file naming convention, if applicable:
Files are named as:
<scene identifier>.<bands>_<width>_<height>_<data type>_<endianness>_<is RGB?>.raw
Where data types are 1 (unsigned 8-bit integers), 2 (unsigned 16-bit integers), 3 (signed 16-bit integers), 4 (signed 32-bit integers), 5 (signed 64-bit integers), 6 (32-bit floating point numbers) or 7 (64-bit floating point numbers). Endianness is 0 for big endian and 1 for little endian.


2. File List:
LC08_L1GT_001075_20150324_20170411_01_T2_b1-7.7_4096_4096_2_1_0.raw
LC08_L1GT_001080_20210815_20210826_01_T2_b1-7.7_4096_4096_2_1_0.raw
LC08_L1GT_004064_20140630_20170421_01_T2_b1-7.7_4096_4096_2_1_0.raw
LC08_L1GT_007020_20140619_20170421_01_T2_b1-7.7_4096_4096_2_1_0.raw
LC08_L1GT_007020_20160507_20170325_01_T2_b1-7.7_4096_4096_2_1_0.raw
LC08_L1GT_007020_20160608_20170324_01_T2_b1-7.7_4096_4096_2_1_0.raw
LC08_L1GT_007020_20160624_20170323_01_T2_b1-7.7_4096_4096_2_1_0.raw
LC08_L1GT_025023_20170217_20170228_01_T2_b1-7.7_4096_4096_2_1_0.raw
LC08_L1GT_025029_20151229_20170224_01_T2_b1-7.7_4096_4096_2_1_0.raw
LC08_L1GT_035022_20180109_20180119_01_T2_b1-7.7_4096_4096_2_1_0.raw
LC08_L1GT_035027_20200319_20200326_01_T2_b1-7.7_4096_4096_2_1_0.raw
LC08_L1GT_035035_20190520_20190604_01_T2_b1-7.7_4096_4096_2_1_0.raw
LC08_L1GT_037028_20181225_20190129_01_T2_b1-7.7_4096_4096_2_1_0.raw
LC08_L1GT_037031_20161117_20170219_01_T2_b1-7.7_4096_4096_2_1_0.raw
LC08_L1GT_045014_20140917_20170303_01_T2_b1-7.7_4096_4096_2_1_0.raw
LC08_L1GT_175025_20140204_20170426_01_T2_b1-7.7_4096_4096_2_1_0.raw
LC08_L1GT_196031_20130322_20170505_01_T2_b1-7.7_4096_4096_2_1_0.raw
LC08_L1GT_196031_20131103_20170428_01_T2_b1-7.7_4096_4096_2_1_0.raw
LC08_L1GT_197031_20170427_20170515_01_T2_b1-7.7_4096_4096_2_1_0.raw
LC08_L1GT_198031_20150904_20180527_01_T2_b1-7.7_4096_4096_2_1_0.raw
LC08_L1GT_198031_20200121_20200128_01_T2_b1-7.7_4096_4096_2_1_0.raw


3. Relationship between files:
N/A


4. File format:
RAW data.



TABULAR DATA-SPECIFIC INFORMATION
---------------------------------

1. File name:
N/A


2. Number of rows and columns: 
N/A


3. Variable list:
N/A


4. Missing data codes:
N/A

        
5. Specialized formats or abbreviations used:
N/A 



MORE INFORMATION 
----------------
N/A
