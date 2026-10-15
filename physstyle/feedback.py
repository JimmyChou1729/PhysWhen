"""Validate local reader exports; importing never establishes a readability effect."""
from pathlib import Path
from .common import *
def validate_v1(obj,manifest):
 if not isinstance(obj,dict) or obj.get('schema')!='physwhen.feedback.v1':raise ValueError('unsupported feedback schema')
 if obj.get('dataset_id')!=manifest['dataset_id']:raise ValueError('wrong reader dataset')
 if obj.get('test_mode') is not False:raise ValueError('test or unspecified provenance; not a real reader export')
 if not isinstance(obj.get('reader_id'),str) or len(obj['reader_id'])>80:raise ValueError('invalid reader code')
 valid={f'C{i}:{v}' for i in range(1,4) for v in ['P','Q']}
 if not isinstance(obj.get('texts'),dict) or set(obj['texts'])-valid:raise ValueError('invalid text identities')
 for record in obj['texts'].values():
  if not isinstance(record,dict) or type(record.get('complete')) is not bool:raise ValueError('invalid completion flag')
  if record.get('effort') not in ('','1','2','3','4','5','unfamiliar'):raise ValueError('invalid effort')
  answers=record.get('answers')
  if not isinstance(answers,dict) or set(answers)-{'Q1','Q2','Q3'}:raise ValueError('invalid question IDs')
  if any(not isinstance(t,str) or len(t)>20000 for t in list(answers.values())+[record.get('friction')]):raise ValueError('invalid text field')
 comparisons=obj.get('comparisons')
 if not isinstance(comparisons,dict) or set(comparisons)-{'C1','C2','C3'}:raise ValueError('invalid case IDs')
 for item in comparisons.values():
  if not isinstance(item,dict) or item.get('preference') not in ('','P','Q','tie','uncertain') or not isinstance(item.get('note'),str) or len(item['note'])>20000:raise ValueError('invalid comparison')
 return obj

def validate_feedback(obj,manifest):
 if isinstance(obj,dict) and obj.get('schema')=='physwhen.feedback.v1':return validate_v1(obj,manifest)
 from .group_feedback import validate_v2
 return validate_v2(obj,manifest)

def import_feedback(path):
 from .group_feedback import import_path
 return import_path(path)
