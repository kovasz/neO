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
