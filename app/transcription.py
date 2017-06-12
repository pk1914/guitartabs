import librosa
import librosa.display
import matplotlib.pyplot as plt
import essentia
import essentia.standard as ess
from music21 import *
from librosa.core import hz_to_note, time_to_frames, frames_to_time
from onset import get_onset_frames
from pitch import get_pitches
from chords import get_chords
from duration import get_durations
from sklearn.decomposition import NMF
from filter import bandpass_filter, remove_noise
from util import *
from scipy.signal import medfilt

def transcribe(filename):
  sr = 44100
  environment.set('musicxmlPath', '/usr/bin/musescore')

  y, sr = librosa.load(filename, sr=sr)

  # NMF:
  #D = librosa.core.stft(y)
  #n_components = 5

  #W, H = librosa.decompose.decompose(np.abs(D), n_components=n_components, sort=True)

  #print W.shape
  #print H.shape

  #for n in range(n_components):
  #  plt.subplot(np.ceil(n_components/2.0), 2, n+1)
  #  plt.plot(W[:, n])
  #  plt.ylim(0, W.max())
  #  # plt.xlim(0, W.shape[0])
  #  plt.xscale('log', basex=2)

  #  plt.ylabel('Component {}'.format(n))

  #plt.show()

  #for n in range(n_components):
  #  plt.subplot(np.ceil(n_components/2.0), 2, n+1)
  #  plt.plot(H[n])
  #  plt.ylim(0, H.max())
  #  plt.xlim(0, H.shape[1])
  #  plt.ylabel('Component {}'.format(n))

  #plt.show()

  # Get tempo
  tempo = get_tempo(y)

  # Get key
  key = get_key(y)

  # Get onset times
  onset_frames = get_onset_frames(y, sr)

  # print frames_to_time(onset_frames, sr)

  print len(onset_frames)

  durations = get_durations(onset_frames, tempo)

  # Filter the signal.
  filtered_y = bandpass_filter(y, sr, 80., 4000.)

  # chords = get_chords(filename, filtered_y, sr)
  # print chords

  #print "UNFILTERED:"
  #pitches = get_pitches(y, sr, onset_frames, 'min_stft')
  #print "MIN_STFT: {}".format(pitches)
  #pitches = get_pitches(y, sr, onset_frames, 'autocorr')
  #print "AUTOCORR: {}".format(pitches)
  #pitches = get_pitches(y, sr, onset_frames, 'yin')
  #print "YIN: {}".format(pitches)
  #print "-----------------------"
  #print "FILTERED:"
  # Detect pitch with different methods:
  #pitches = get_pitches(filtered_y, sr, onset_frames, 'min_stft')
  #print "MIN_STFT: {}".format(pitches)
  # pitches = get_pitches(filtered_y, sr, onset_frames, 'autocorr')
  # print "AUTOCORR: {}".format(pitches)
  #pitches = get_pitches(filtered_y, sr, onset_frames, 'yin')
  # print "YIN: {}".format(pitches)
  
  pitches = get_pitches(filtered_y, sr, onset_frames, 'autocorr')

  notes = pitches_to_notes(pitches)

  # Convert to Music21 stream and export to MusicXML file.
  score = get_score(notes, durations, tempo)

  score.write("musicxml", "static/piece.mxl")

  # plot_waveform(filtered_y)
  # plot_spectrogram(librosa.stft(filtered_y), sr)
  plt.close('all')
  
  return notes

def get_score(notes, durations, quarter_length):
  score = stream.Score()
  score.insert(0, clef.Treble8vbClef())
  # Time Signature
  # Key Signature
  score.insert(instrument.Guitar())
  score.insert(0, tempo.MetronomeMark(number=quarter_length))
  #score.insert(0, key.KeySignature(-1))
  #score.insert(0, meter.TimeSignature('2/4'))
  notes = sum(notes, [])
  for i in range(0, len(notes)):
    f = note.Note(notes[i])
    print durations[i]
    f.duration = duration.Duration(durations[i])
    score.append(f)

  return score

def get_tempo(y):
  tempo_estimator = ess.PercivalBpmEstimator()
  bpm = tempo_estimator(y)
  # print "Not rounded: {}".format(bpm)
  bpm = round_to_base(bpm, 5)
  if bpm < 60:
    bpm = bpm * 2
  elif bpm > 220:
    bpm = bpm / 2
  return round_to_base(bpm, 5)

def get_key(y):
  key_extractor = ess.KeyExtractor()
  key = key_extractor(essentia.array(y))
  # print key
  return key