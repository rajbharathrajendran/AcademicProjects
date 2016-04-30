import sys
import os
import codecs
import re
import string

class pos:
	def preproInsertSpace(self,input):
		strwithspace=""
		for i in range(0,len(input)):
			if input[i] == '.'.encode("utf-8") and input[i+1] != ' '.encode("utf-8"):
				if not ((i>0 and input[i-1].isdigit()) and (i<len(input)-1 and input[i+1].isdigit())):				
					strwithspace+=input[i]+' '.encode("utf-8")
				else:
					strwithspace+=input[i]
			elif(input[i] == ','.encode("utf-8") and input[i+1] != ' '.encode("utf-8")):
				if  not ((i>0 and input[i-1].isdigit()) and (i<len(input)-1 and input[i+1].isdigit())):			
					strwithspace+=input[i]+' '.encode("utf-8")
			elif input[i] == ','.encode("utf-8"):
				if  ((i>0 and input[i-1] == ' ') and (i<len(input)-1 and input[i+1] == ' ')):
					tmpstr = strwithspace		
					strwithspace = tmpstr.strip()+input[i]+' '.encode("utf-8")
				else:
					strwithspace+=input[i]
			elif(input[i] == ';'.encode("utf-8") and input[i+1] != ' '.encode("utf-8")):
				strwithspace+=input[i]+' '.encode("utf-8")
			elif (input[i] == '\n'.encode("utf-8") and (input[i-2]+input[i-1]!='. '.encode("utf-8") or input[i-1]!='.'.encode("utf-8"))):
				strwithspace+=". ".encode("utf-8")
			else:
				strwithspace+=input[i]
		return strwithspace

	def split(self,strwithspace):
		ustr=strwithspace[0:3]
		i=3
		while i <(len(strwithspace)-1):
			if strwithspace[i]+strwithspace[i+1] == '. '.encode("utf-8"):
				if strwithspace[i-1].isdigit():
					ustr += strwithspace[i+1]
					i=i+2
				elif strwithspace[i+1].isdigit():
					ustr += strwithspace[i]
					i=i+1
				elif strwithspace[i-3] == ' '.encode("utf-8") or strwithspace[i-2] == ' '.encode("utf-8"):
					if i+2 < len(strwithspace) and strwithspace[i + 2].isdigit():
						i=i+1
					else:
						i=i+2
				else:		
					ustr += strwithspace[i]
					i=i+1
			else:
				ustr+=strwithspace[i]
				i=i+1
		splitinput=ustr.split(". ")
		return splitinput

	def parseposout(self,posout,final,tempwordsplit):
		index=0
		out=posout.split("\n")
		for line in out:
			if "SYM".encode('utf-8') in line:
				continue;
			token=line.split()
			if len(token) != 0 and ".".encode("utf-8") in token[0]:
				word=token[1]	
				print(word+" "+tempwordsplit[index])					
				tempwordsplit[index]=tempwordsplit[index].encode('utf-8').translate(None,'"*+<=>^`\'{|}~')
				tempwordsplit[index]=tempwordsplit[index].decode("utf-8")
				if  word == tempwordsplit[index]:
					final.write(word+" "+token[2]+" ")
					if len(token) > 4:
						m=re.search(r"(?<=af=').*,",token[4],re.UNICODE)
						if(m is not None):
							rootlist=m.group(0).split(",")
							final.write(rootlist[0]+" "+rootlist[len(rootlist)-2]+"\n")
					index=index+1
				elif  word in tempwordsplit[index]:
					if(re.search(r'-|/|\\|_|:',tempwordsplit[index],re.UNICODE) != None):
						final.write(tempwordsplit[index]+" "+token[2]+" ")
						final.write(tempwordsplit[index]+"\n")
						index+=1
					elif(re.search(r'\?|!|,|;',tempwordsplit[index],re.UNICODE) != None):
						final.write(word+" "+token[2]+" ")
						if len(token) > 4:
							m=re.search(r"(?<=af=').*,",token[4],re.UNICODE)
							if(m is not None):
								rootlist=m.group(0).split(",")
								final.write(rootlist[0]+" "+rootlist[len(rootlist)-2]+"\n")
						word=tempwordsplit[index][len(tempwordsplit[index])-1]
						final.write(word+" SYM "+word+"\n")
						index=index+1
				elif tempwordsplit[index] in word and tempwordsplit[index+1].encode('utf-8').translate(None,',"?!,;').decode("utf-8") in word:
					final.write(tempwordsplit[index]+" "+token[2]+" ")
					if len(token) > 4:
						m=re.search(r"(?<=af=').*,",token[4],re.UNICODE)
						if(m is not None):
							rootlist=m.group(0).split(",")
							final.write(rootlist[0]+" "+rootlist[len(rootlist)-2]+"\n")
					index=index+1
					final.write(tempwordsplit[index]+" "+token[2]+" ")
					final.write(tempwordsplit[index]+"\n")
					index=index+1
					
						
		final.write("\n")
		
def main():
	posobj=pos()
	for root,direc,filelist in os.walk(sys.argv[1]):
        	for file in filelist:
          		if file.endswith('.txt'):
				f = codecs.open(os.path.join(root,file), "r", "utf-8")
  				input=f.read()
				strwithspace=posobj.preproInsertSpace(input)						
				splitinput=posobj.split(strwithspace)
				final=codecs.open("output/"+file.split(".")[0]+".pos", "w", "utf-8")
				for line_no in range(0,len(splitinput)-1):
					fpw=codecs.open("output.txt", "w", "utf-8")
					fpw.write(splitinput[line_no])
					fpw.close()
					os.system("shallow_parser_tam output.txt posout.txt")
					tempwordsplit=splitinput[line_no].split()
					fpwp=codecs.open("posout.txt", "r", "utf-8")
					posout=fpwp.read()
					posobj.parseposout(posout,final,tempwordsplit)	
					fpwp.close()				
				

if __name__ == "__main__":main()
