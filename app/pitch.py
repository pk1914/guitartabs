import librosa
import numpy as np
from librosa.core import frames_to_time
from frequency_estimator import freq_from_hps, freq_from_autocorr, other_autocorr

# Checking the pitch some frames the onset time increased precision.
def detect_pitch(y, sr, onset_frames, method='stft', stft_offset=10, fmin=80, fmax=4000):
  result_pitches = []

  pitches, magnitudes = librosa.piptrack(y=y, 
    sr=sr, fmin=fmin, fmax=fmax)

  if method == 'stft':
    for i in range(0, len(onset_frames)):
      onset = onset_frames[i] + stft_offset
      index = magnitudes[:, onset].argmax()
      pitch = pitches[index, onset]
      # duration = detect_duration(magnitudes, index, onset)
      if (pitch != 0):
        result_pitches.append(pitch)

  elif method == 'autocorr':
    slices = segment_signal(y, sr, onset_frames)
    for segment in slices:
      pitch = freq_from_autocorr(segment, sr)
      result_pitches.append(pitch)

  elif method == 'hps':
    slices = segment_signal(y, sr, onset_frames)
    for segment in slices:
      pitch = freq_from_hps(segment, sr)
      result_pitches.append(pitch)
      # Fixing estimation error:
      pitches = remove_values_from_list(result_pitches, 0.)
      result_pitches = [pitch + 10 for pitch in result_pitches]

  elif method == 'min_stft':
    # Getting the first N peaks. Choose the minimum one in terms of frequency.
    candidates = get_peaks(pitches, magnitudes, onset_frames)
    print candidates
    for c in candidates:
      chord = is_chord(c)
      pitch = min(c)
      result_pitches.append(pitch)

  return result_pitches

# For each note played, get the n strongest peaks in the frequency spectrum.
def get_peaks(pitches, magnitudes, onset_frames, n=4, offset=10):
    candidate_list = []

    for i in range(0, len(onset_frames)):
      candidates = []
      onset = onset_frames[i] + offset
      indices = np.argpartition(magnitudes[:, onset], 0-n)[0-n:]

      for j in indices:
        # print "{} at frame {}: {}".format(pitches[j, onset], onset, magnitudes[j, onset])
        candidates.append(pitches[j, onset])

      candidates = remove_values_from_list(candidates, 0)

      candidate_list.append(candidates)

    return candidate_list

def segment_signal(y, sr, onset_frames, from_minima=False, offset_start=0.01,
  offset_end=0.1):

  if from_minima:
    # We split the signal into slices that sum up to the whole signal
    # according to onset_bt (from local minima to the next local minima).
    oenv = librosa.onset.onset_strength(y=y, sr=sr)
    onset_bt = librosa.onset.onset_backtrack(onset_frames, oenv)
    new_onset_bt = librosa.frames_to_samples(onset_bt)

    slices = np.split(y, new_onset_bt[1:])

  else:
    # We split the signal into slices that span from peak p + offset_start
    # to p + offset_end.
    offset_start_frames = int(librosa.time_to_samples(offset_start, sr))
    offset_end_frames = int(librosa.time_to_samples(offset_end, sr))

    slices = np.array([y[i + offset_start_frames : i + offset_end_frames] for i
      in librosa.frames_to_samples(onset_frames)])

  return slices

def remove_values_from_list(l, val):
  return [value for value in l if value != val]

def is_chord(candidate):
  candidate.sort()
  print candidate

  if len(candidate) == 1:
    return False
  else:
    mid = candidate[1]
    min = candidate[0]
    
    div = mid / min
    inharmonicity_factor = abs(round(div) - div)

    print "MID WITH MIN:"
    print inharmonicity_factor

    if len(candidate) == 3:
      max = candidate[2]
      div = max / min
      print div
      inharmonicity_factor = abs(round(div) - div)

      print "MAX WITH MIN:"
      print inharmonicity_factor

