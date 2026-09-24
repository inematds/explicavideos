import unittest,sys,json
from pathlib import Path
from unittest.mock import patch
from io import BytesIO
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'engine'))
import heygen_read
class ReadRetry(unittest.TestCase):
 def test_timeout_then_success(self):
  with patch.object(heygen_read.urllib.request,'urlopen',side_effect=[TimeoutError(),BytesIO(b'{"data":{"status":"pending"}}')]) as request,patch.object(heygen_read.time,'sleep'):
   self.assertEqual(heygen_read.get('/v3/videos/test')['data']['status'],'pending')
   self.assertEqual(request.call_count,2)
 def test_exhaustion_returns_status_without_crashing(self):
  with patch.object(heygen_read.urllib.request,'urlopen',side_effect=TimeoutError()) as request,patch.object(heygen_read.time,'sleep'):
   self.assertEqual(heygen_read.get('/v3/videos/test')['status'],'unavailable')
   self.assertEqual(request.call_count,3)
