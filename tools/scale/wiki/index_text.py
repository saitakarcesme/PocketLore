"""Index-only omission of the reader's already ignored query words.

Stored text and title remain unchanged. This policy is not a language stemmer.
"""
import re
STOP=frozenset('a an the is are of to in and or for from with what how why which when does do by on at as into explain compare between'.split())
_PATTERN=re.compile(r'(?<![^\W_])(?:'+ '|'.join(sorted(STOP,key=len,reverse=True))+r')(?![^\W_])',re.I)
def body(text):
 return _PATTERN.sub(lambda m:' ' if m.group().casefold() in STOP else m.group(),text)
