# Named Entity Recognizers for historical articles in Tamil

The Project has 4 modules

* Crawler  ==> NLP/Crawler

Create a Java Project and include Crawler 4j Jar for dependency
https://drive.google.com/file/d/0B81L1OwkX30RWVh2RXJJSzJWRGM/view?usp=sharing   --> Crawler 4j Jar

* NER Tool

https://github.com/kumarse/NER-TagUI

* POS/Root Words/Suffix/Boolean Suffix

NLP/Scripts/pos.py
This is the script which takes txt files as input and run POS shallow parser to obtain POS tags/Root words and suffixes

--command_line_input => NLP/Data/Raw/

It generates filename.pos as output

All ".pos" files for training and test set is put up in NLP/Data/POS/ folder.

* Combine all results :-

NLP/Scripts/combine.py
This is the script which combines output from Module 2 and 3 then prepares input file for CRF++

--> command_line_input => NLP/Data/NER/ NLP/Data/POS/


* run CRF++
We used CRF++ Tool for our project
https://taku910.github.io/crfpp/

It needs training file, template file , model file and test file

We obtained 72.89% as our final result

The files are in the following path
```sh
training file --> NLP/Data/CRF/training/train4.txt
template file --> NLP/Data/CRFTemplate/temp3.txt
model file    --> NLP/Data/CRF/model/model173.txt
test file     --> NLP/Data/CRF/test/test4.txt
```

NLP/Scripts/accuracy.py
This is the script which calculates the accuracy of the result

