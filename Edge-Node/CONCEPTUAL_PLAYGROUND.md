# Conceptual Framework: Edge Node Playground Environment

## 1. Platform Context

EdgeSDR-Nexus is a spectral monitoring platform operated by Colombia's national spectrum regulatory authority (ANE). Its purpose is the systematic acquisition, analysis, and reporting of radio-frequency emissions across the national territory. The platform is organized into five major subsystems: a frontend operator dashboard, a backend REST/WebSocket API, a post-processing microservice for spectral analysis and compliance evaluation, an infrastructure layer for orchestration and deployment, and a network of edge-deployed RF sensors. The edge sensors, implemented as Raspberry Pi 5 units coupled with HackRF One software-defined radios, constitute the data-acquisition front-end of the entire system. They are responsible for tuning to specified frequency bands, capturing raw IQ samples, computing power spectral density estimates, optionally demodulating broadcast audio, and transmitting all results to a central server for storage and further analysis.

The edge node employs a hybrid architecture in which a high-performance C data plane handles all time-critical operations — hardware control, sample acquisition, ring-buffer management, and digital signal processing — while a Python control plane manages orchestration, scheduling, state transitions, network communication, and resilience. The two planes communicate through a ZeroMQ request-reply channel over a local inter-process socket, with the Python side issuing JSON-encoded configuration payloads and the C side returning processed results.

## 2. The Playground Environment: Purpose and Scope

The `playground/` directory within the edge node constitutes a self-contained experimental environment designed to facilitate the development, validation, and pedagogical exploration of signal-processing algorithms and RF engine capabilities without requiring deployment to production sensor hardware. It comprises three progressively sophisticated test scripts and a companion tutorial document, each addressing a distinct mode of interaction with the RF engine.

The playground serves three concurrent objectives:

- **Algorithm development**: providing researchers and engineers with a controlled substrate on which to prototype spectral analysis methods, compare PSD estimation techniques, and validate custom DSP pipelines against known reference signals.
- **Engine verification**: enabling systematic validation of the RF engine's request-response contract, processing modes, and error handling under reproducible conditions, independent of hardware availability and network dependencies.
- **Pedagogical onboarding**: lowering the barrier to entry for new contributors by presenting the platform's IPC protocol, signal representations, and processing modes through hands-on, progressively complex examples.

## 3. Processing Modalities

The RF engine exposes three distinct processing modalities, each representing a different level of abstraction in the signal-acquisition and analysis chain. These modalities form a hierarchy of data granularity and computational responsibility.

### 3.1 Power Spectral Density Mode

In PSD mode, the RF engine performs the complete signal-processing chain internally: it acquires IQ samples from the HackRF hardware (or from a synthetic source in dry-run mode), applies IQ compensation, executes the selected spectral estimation algorithm (Welch's method or polyphase filter bank), and returns a frequency-domain power representation. The output is a vector of power spectral density values, one per frequency bin, expressed in dBm relative to the digital ADC scale. This mode represents the highest level of abstraction, where the caller receives a processed spectral characterization rather than raw sample data.

Two spectral estimation methods are available. Welch's method partitions the input into overlapping windowed segments, computes the periodogram of each, and averages them, trading spectral resolution for reduced variance. The polyphase filterbank method employs a bank of FIR filters to decompose the signal into frequency channels with superior sidelobe rejection and inter-bin isolation, at the cost of increased computational complexity. The selection between these methods represents a fundamental tradeoff in spectral analysis between estimation quality and processing overhead.

### 3.2 Raw IQ Mode

In IQ mode, the engine returns the acquired complex samples without performing spectral estimation. The output is an interleaved sequence of real and imaginary components, representing the baseband signal as captured by the ADC after frequency down-conversion, IQ compensation, and optional filtering. This mode preserves the full informational content of the acquired signal, enabling the caller to perform arbitrary downstream processing — custom PSD estimation, modulation classification, signal detection, or any other algorithm that operates on time-domain complex samples.

IQ mode is conceptually significant because it decouples the acquisition layer from the analysis layer. By exposing raw samples, the platform enables the development of third-party analysis algorithms that can be validated against known signals in the playground environment before being integrated into the production pipeline. It also permits the comparison of different spectral estimation techniques applied to identical input data.

### 3.3 Audio Demodulation Mode

The engine additionally supports FM and AM broadcast demodulation, producing PCM audio output encoded in Opus format and transmitted over TCP. While not directly exercised by the playground scripts, this mode represents a third processing path that shares the same acquisition infrastructure. The audio pipeline operates on a separate ring buffer, enabling concurrent PSD and demodulation without mutual interference.

## 4. The Dry-Run Paradigm

A central methodological contribution of the playground environment is its exploitation of the RF engine's dry-run capability. In dry-run mode, the engine bypasses all hardware interaction — no HackRF initialization, no USB communication, no RF tuning — and instead processes a caller-provided synthetic IQ vector through the identical DSP pipeline used for live acquisitions.

This paradigm has several methodological implications:

- **Reproducibility**: synthetic signals with known parameters (frequency, amplitude, phase, noise characteristics) enable deterministic validation of processing algorithms. Results can be compared against analytical expectations without the stochastic variability inherent in over-the-air reception.
- **Isolation**: by removing the hardware layer, dry-run mode isolates algorithmic behavior from hardware artifacts (gain drift, LO leakage, ADC nonlinearity, USB transfer jitter), enabling focused debugging of the digital signal processing chain.
- **Accessibility**: dry-run mode permits the full processing pipeline to be exercised on any Linux desktop without HackRF hardware, democratizing participation in algorithm development and platform validation.
- **Regression testing**: known input-output pairs established through dry-run experiments can serve as reference fixtures for continuous validation of engine modifications.

The dry-run mechanism preserves the structural integrity of the entire processing pipeline. The synthetic IQ vector passes through the same parser, ring buffer, IQ compensation, optional channel filtering, and spectral estimation stages as live data. The only difference is the source of samples: a Python-generated array rather than the HackRF receiver callback.

## 5. Script Taxonomy and Progressive Complexity

The three playground scripts implement a deliberate pedagogical progression, each building upon the conceptual foundations established by its predecessors.

### 5.1 Script One: PSD Request via Polyphase Filterbank

The first script establishes the baseline interaction pattern with the RF engine. It constructs a minimal PSD request specifying center frequency, sample rate, spectral estimation method, resolution bandwidth, window function, and hardware gain parameters, and transmits it through the ZeroMQ IPC channel. The script demonstrates the synchronous request-reply protocol, the structure of the JSON configuration payload, and the interpretation of the returned spectral data.

This script operates in live mode, requiring both the RF engine process and a connected HackRF device. It serves as the simplest possible end-to-end test of the hardware-acquisition-to-spectral-result pipeline.

### 5.2 Script Two: Dry-Run Multi-Mode Demonstration

The second script substantially extends the conceptual scope by introducing the dry-run paradigm and exercising all three processing modalities within a single session. It constructs a synthetic two-tone signal — a superposition of 1 kHz and 5 kHz sinusoids at specified amplitudes — and submits it to the RF engine through three successive requests, each targeting a different processing mode.

The first request invokes IQ mode, demonstrating that the synthetic signal traverses the engine's processing pipeline and returns as raw complex samples. The second request invokes Welch PSD mode, showing how the same signal is characterized spectrally through averaged periodograms. The third request invokes PFB PSD mode, enabling direct comparison of the two spectral estimation methods applied to identical input data.

This multi-mode demonstration is methodologically important because it enables the caller to verify that all three processing paths produce consistent, interpretable results for a known reference signal. The two-tone input has a precisely defined spectral signature — two discrete peaks at 1 kHz and 5 kHz — against which the output of each processing mode can be validated. Any discrepancy between the modes, or between the observed and expected peak locations, would indicate a processing error in the corresponding pipeline.

### 5.3 Script Three: Live IQ Acquisition and Spectral Analysis

The third script completes the progression by acquiring real RF data from a connected HackRF device in IQ mode and performing independent spectral analysis using Python-side Welch estimation. This script demonstrates the end-to-end workflow for algorithm development: hardware acquisition through the engine, raw sample retrieval, and custom downstream processing.

The script applies a Welch PSD estimate to the received complex samples using scipy's Welch implementation, performs peak detection with prominence-based ranking, and generates a publication-quality spectral plot. This establishes the reference workflow for developing and validating custom analysis algorithms: acquire through the engine, process independently, compare against the engine's own PSD output, and visualize the results.

## 6. Inter-Process Communication Protocol

All playground scripts interact with the RF engine through a ZeroMQ request-reply channel bound to the inter-process address `ipc:///tmp/rf_engine`. The protocol is symmetric in structure but asymmetric in role: the Python script acts as the requester (ZMQ REQ socket), and the C engine acts as the replier (ZMQ REP socket).

The communication follows a strict synchronous pattern: the requester sends a single JSON-encoded configuration string, blocks until a response arrives (with a configurable timeout), and then processes the result. The engine, upon receiving a request, parses the configuration, executes the corresponding processing pipeline, serializes the result as JSON, and sends it back through the same channel.

This protocol design reflects the request-driven architecture of the overall system. In production, the central server issues configuration commands to the edge sensor, which processes them and returns results. The playground scripts replicate this interaction pattern exactly, substituting the central server's role with a local Python process. This structural isomorphism ensures that algorithms validated in the playground environment will behave identically when deployed in the production data flow.

## 7. Signal Representation and Data Formats

The platform employs a consistent signal representation throughout its processing chain. HackRF delivers interleaved signed 8-bit IQ samples: `[I0, Q0, I1, Q1, ...]`. The C data plane converts these to double-precision complex values for DSP operations. In IQ mode, the engine returns the processed samples as interleaved floating-point values in the same `[I, Q]` ordering, with length equal to twice the number of complex samples.

PSD results are returned as a one-dimensional array of power spectral density values, one per frequency bin, spanning the captured bandwidth from the lower to the upper frequency boundary. The frequency axis is implicitly defined by the center frequency, sample rate, and number of FFT bins. Values are expressed in dBm relative to the digital ADC scale; absolute power calibration requires external reference measurements.

The dry-run mode accepts synthetic IQ data in the same interleaved format, with the constraint that the array length must be even (each complex sample requires both an I and a Q component). The amplitude range of the synthetic signal must account for the integer quantization that occurs when the engine casts floating-point values to the internal 8-bit representation: signals with amplitude below approximately 1.0 will be quantized to zero.

## 8. Spectral Estimation Methodology

### 8.1 Welch's Method

Welch's method estimates the power spectral density by partitioning the input signal into overlapping segments, applying a window function to each, computing the squared magnitude of the discrete Fourier transform, and averaging the resulting periodograms. The method reduces the variance of the spectral estimate at the expense of frequency resolution, with the degree of smoothing controlled by the segment length (FFT size), overlap ratio, and window function.

The FFT size is derived from the requested resolution bandwidth and the sample rate, ensuring that the resulting frequency bins have the specified width. Supported window functions include Hamming, Hann, Blackman, Flat Top, Kaiser, Tukey, Bartlett, and rectangular, each offering different tradeoffs between main-lobe width and sidelobe attenuation. The implementation uses FFTW3 for transform computation and OpenMP for parallel segment processing.

### 8.2 Polyphase Filterbank Method

The polyphase filterbank method decomposes the input signal into frequency channels using a bank of polyphase FIR filters derived from a prototype lowpass filter. Each channel is independently transformed and the results are aggregated to produce the spectral estimate. This method provides superior inter-channel isolation and sidelobe rejection compared to Welch's method, at the cost of increased memory and computational requirements.

The prototype filter is a Kaiser-windowed FIR design with configurable taps per channel. The filterbank structure naturally aligns with the FFT, enabling efficient implementation through polyphase decomposition. The resulting spectral estimate has uniform frequency resolution across the entire bandwidth, with each bin corresponding to a well-defined filter channel rather than a Fourier coefficient.

### 8.3 Comparative Considerations

The choice between Welch and PFB methods reflects a fundamental tradeoff in spectral analysis. Welch's method is computationally efficient and provides good variance reduction through segment averaging, making it suitable for general-purpose monitoring where moderate spectral resolution suffices. The PFB method offers sharper frequency discrimination and better rejection of out-of-band interference, making it preferable when the monitored spectrum contains closely spaced emissions or when precise power measurement in individual channels is required.

The playground environment enables direct comparison of both methods applied to identical input data, facilitating informed method selection for specific monitoring scenarios. This comparative capability is particularly valuable for calibrating the platform's spectral analysis pipeline against known reference signals.

## 9. Calibration and Error Compensation

The RF engine incorporates multiple layers of error compensation that are transparent to the playground user but fundamentally affect the quality of acquired data. IQ compensation removes DC offset, gain imbalance, and phase quadrature errors from each processing block before spectral estimation. This blind, block-by-block correction improves the central DC spike behavior and image rejection without requiring external calibration references.

For continuous audio processing, a streaming DC blocker with single-pole IIR filtering provides stateful offset removal that avoids the discontinuities inherent in block-by-block mean subtraction. The audio demodulators additionally apply their own DC blockers after demodulation to remove residual low-frequency offsets.

Post-acquisition, the Python control plane applies adaptive DC spike repair to the returned PSD arrays, detecting and reconstructing the central bins that may contain residual LO leakage artifacts. This layered compensation strategy — time-domain IQ correction, streaming DC blocking, and post-PSD repair — addresses the DC offset problem at multiple points in the processing chain, each layer targeting artifacts that the preceding layers cannot fully eliminate.

The platform also supports PPM frequency correction, estimated through an automated calibration procedure that identifies FM broadcast pilots and measures frequency offset. This correction is applied at the hardware tuning stage and does not affect the playground environment's dry-run mode, where frequency accuracy is determined entirely by the synthetic signal generation.

## 10. Architectural Significance of the Playground

The playground environment embodies a broader architectural principle: the separation of concerns between acquisition, processing, and presentation. By exposing raw IQ data and enabling dry-run processing, the platform decouples these three concerns and permits independent development and validation of each.

This separation is not merely a convenience but a structural necessity for a system that must operate across heterogeneous environments — from desktop development workstations to remote Raspberry Pi sensors deployed across the national territory. The playground provides the bridge between these environments, enabling algorithm development in the former and deployment in the latter without structural modification to the processing pipeline.

Furthermore, the playground establishes a testing methodology that scales with the platform's evolution. As new spectral estimation methods, demodulation algorithms, or analysis techniques are added to the RF engine, they can be immediately exercised through the playground's multi-mode testing framework. The dry-run paradigm ensures that new capabilities can be validated against known signals before being exposed to the variability of live hardware acquisition.

The progressive complexity of the three scripts — from a single PSD request, through multi-mode comparison, to live acquisition with independent analysis — mirrors the natural workflow of a researcher or engineer engaging with the platform. This deliberate structure transforms the playground from a collection of test scripts into a coherent methodological framework for signal-processing development within the EdgeSDR-Nexus ecosystem.
