# CREATED: 11/9/15 3:57 PM by Justin Salamon <justin.salamon@nyu.edu>

import librosa, vamp
import argparse
import numpy as np
from midiutil.MidiFile import MIDIFile

def save_midi(outfile, notes, tempo):

    track = 0
    time = 0
    MIDI = MIDIFile(1)

    # Add track name and tempo.
    MIDI.addTrackName(track, time, "MIDI TRACK")
    MIDI.addTempo(track, time, tempo)

    channel = 0
    volume = 100

    for note in notes:
        onset = note[0] * (tempo/60.)
        duration = note[1] * (tempo/60.)
        # duration = 1
        pitch = note[2]
        MIDI.addNote(track, channel, pitch, onset, duration, volume)

    # And write it to disk.
    binfile = open(outfile, 'wb')
    MIDI.writeFile(binfile)
    binfile.close()


def midi_to_notes(midi, fs, hop):

    notes = []
    p_prev = None
    duration = 0
    onset = 0
    for n, p in enumerate(midi):
        if p==p_prev:
            duration += 1
        else:
            # treat 0 as silence
            if p_prev > 0:
                # add note
                duration_sec = duration * hop / float(fs)
                onset_sec = onset * hop / float(fs)
                notes.append((onset_sec, duration_sec, p_prev))

            # start new note
            onset = n
            duration = 1
            p_prev = p

    # add last note
    if p_prev > 0:
        # add note
        duration_sec = duration * hop / float(fs)
        onset_sec = onset * hop / float(fs)
        notes.append((onset_sec, duration_sec, p_prev))

    return notes


def hz2midi(hz):

    # convert from Hz to midi note
    hz_nonneg = hz.copy()
    hz_nonneg[hz<=0] = 0
    midi = 69 + 12*np.log2(hz_nonneg/440.)
    midi[midi<=0] = 0

    # round
    midi = np.round(midi)

    return midi


def audio_to_midi_melodia(infile, outfile):

    # define analysis parameters
    fs = 44100
    hop = 128

    # load audio using librosa
    print("Loading audio...")
    data, sr = librosa.load('/Users/justin/datasets/melody/mirex05/audio/train05.wav', sr=fs, mono=True)

    # extract melody using melodia vamp plugin
    print("Extracting melody f0 with MELODIA...")
    melody = vamp.collect(data, sr, "mtg-melodia:melodia", parameters={"voicing": 0.2})

    # hop = melody['vector'][0]
    pitch = melody['vector'][1]

    # impute missing 0's to compensate for starting timestamp
    pitch = np.insert(pitch, 0, [0]*8)

    # debug
    # np.asarray(pitch).dump('f0.npy')
    # print(len(pitch))

    # convert f0 to midi notes
    print("Converting Hz to MIDI notes...")
    midi_pitch = hz2midi(pitch)

    # segment sequence into individual midi notes
    notes = midi_to_notes(midi_pitch, fs, hop)

    # save note sequence to a midi file
    print("Saving MIDI to disk...")
    save_midi(outfile, notes, 60)

    print("Conversion complete.")



if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("infile")
    parser.add_argument("outfile")

    args = parser.parse_args()

    audio_to_midi_melodia(args.infile, args.outfile)

