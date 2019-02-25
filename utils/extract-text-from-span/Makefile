all:

test:
	perl -CS AIDA-ExtractTextFromSpan-MASTER.pl input/ltf cache input/LDC2018E62.sentence_boundaries.txt HC0003OKL:1-14
	echo "OUTPUT should be =>Наша продукция<="

get-text:
	perl -CS AIDA-ExtractTextFromSpan-MASTER.pl input/ltf cache input/LDC2018E62.sentence_boundaries.txt $(SPAN)
