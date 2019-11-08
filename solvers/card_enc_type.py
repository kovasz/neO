# -*- coding: utf-8 -*-

from enum import Enum
from pysat.card import EncType

class CardEncType(Enum):
	seqcounter = EncType.seqcounter
	sortnetwrk = EncType.sortnetwrk
	cardnetwrk = EncType.cardnetwrk
	mtotalizer = EncType.mtotalizer
	kmtotalizer = EncType.kmtotalizer
#	ownSeqCounter = 102

class Relations(Enum):
	Less = -2
	LessOrEqual = -1
	Greater = 1
	GreaterOrEqual = 2

RelationOps = {
	Relations.Less: "<",
	Relations.LessOrEqual: "<=",
	Relations.Greater: ">",
	Relations.GreaterOrEqual: ">="
}
