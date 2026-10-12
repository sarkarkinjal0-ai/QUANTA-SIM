import numpy as np
from core_engine import CorePhysicsEngine, QuantumState
from photon_noise_engine import PhotonNoiseEngine, NoiseConfig
from physics_experiments import InterferometryExperiments

def test_core_mzi_probability_normalization():
    e = CorePhysicsEngine(2)
    s = QuantumState([1, 0])
    bs = e.create_beam_splitter()
    ps = e.embed_operator(e.create_phase_shifter(np.pi/2), [1])
    out = e.evolve_state(s, [bs, ps, bs])
    assert np.isclose(out.get_probabilities().sum(), 1.0)

def test_hom_50_50_coincidence_zero():
    engine = PhotonNoiseEngine(seed=1)
    result = engine.simulate_hom(reflectivity=0.5)
    assert result["probabilities"]["|1,1>"] < 1e-12

def test_noise_is_bounded_and_reproducible():
    a = PhotonNoiseEngine(NoiseConfig(reflectivity_std=.1), seed=7)
    b = PhotonNoiseEngine(NoiseConfig(reflectivity_std=.1), seed=7)
    assert a.sample_reflectivity(.5) == b.sample_reflectivity(.5)

def test_mzi_contract():
    data = InterferometryExperiments.run_mzi_sweep(noise_std=.0, shots=100, seed=2)
    assert len(data["phi_values"]) == len(data["p0_ideal"])
    assert np.allclose(np.asarray(data["p0_ideal"]) + np.asarray(data["p1_ideal"]), 1.0)

if __name__ == "__main__":
    for fn in [
        test_core_mzi_probability_normalization,
        test_hom_50_50_coincidence_zero,
        test_noise_is_bounded_and_reproducible,
        test_mzi_contract,
    ]:
        fn()
    print("All integration tests passed.")

def test_qiskit_bridge_is_lazy():
    import photon_qiskit_bridge
    assert hasattr(photon_qiskit_bridge, "benchmark_mzi_with_qiskit")

# Optical Builder integration smoke test
from optical_builder.core.builder import mzi_circuit as _mzi_builder
_builder = _mzi_builder(np.pi/2)
assert _builder.is_unitary()
_builder_result = _builder.simulate_single_photon(shots=256)
assert abs(float(np.sum(_builder_result['probabilities'])) - 1.0) < 1e-9
assert sum(_builder.simulate_two_photon(shots=256)['probabilities'].values()) > 0.999999
print('Optical Builder integration test passed.')
