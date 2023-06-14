﻿using System;
using System.IO;
using GroovyCodecs.Mp3;
using GroovyCodecs.WavFile;

namespace GroovyCodecs.Coder
{
	class Program
	{
		private static IMp3Encoder _lameEnc;

		static void Main(string[] args)
		{
			var files =Directory.GetFiles("../testfiles/", "*.wav", SearchOption.AllDirectories);

			foreach(var file in files)
			{
    			_lameEnc = new Mp3Encoder();

    			var audioFile = new WavReader();
				audioFile.OpenFile(file);

    			var srcFormat = audioFile.GetFormat();

    			_lameEnc.SetFormat(srcFormat, srcFormat);

    			var inBuffer = audioFile.readWav();

    			var outBuffer = new byte[inBuffer.Length];

				var timer = new System.Diagnostics.Stopwatch();
				timer.Start();
    			var len = _lameEnc.EncodeBuffer(inBuffer, 0, inBuffer.Length, outBuffer);
				timer.Stop();
                
    	        _lameEnc.Close();

                // _lameDec = new LameDecoder();

                var outFile = File.Create(file + ".mp3");
    			outFile.Write(outBuffer, 0, len);
    			outFile.Close();

				Console.WriteLine($"Converted {file} to MP3 in {timer.ElapsedMilliseconds / 1000}s");
			}
		}
	}

}
