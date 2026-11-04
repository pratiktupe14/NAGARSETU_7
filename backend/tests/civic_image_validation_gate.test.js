const assert = require('assert');
const { evaluateCivicImageDecision, validateCategoryMatch } = require('../src/services/aiService');

console.log('Running Civic Image Validation Gate Unit Tests...\n');

let passed = 0;
let total = 0;

function it(name, fn) {
  total++;
  try {
    fn();
    console.log(`  [PASS] ${name}`);
    passed++;
  } catch (err) {
    console.error(`  [FAIL] ${name}: ${err.message}`);
  }
}

// 1. Genuine Pothole
it('1. Pothole image returns VALID_CIVIC_ISSUE, accepts into evidence, enables auto-fill, disables manual', () => {
  const aiResult = {
    decision_outcome: 'VALID_CIVIC_ISSUE',
    decision_message: 'Civic issue verified and accepted.',
    detected: true,
    detected_class: 'Pothole',
    category: 'Roads',
    confidence: 0.88,
    allow_manual: false,
    accepted_as_evidence: true
  };
  const decision = evaluateCivicImageDecision(aiResult, 'Roads');
  assert.strictEqual(decision.outcome, 'VALID_CIVIC_ISSUE');
  assert.strictEqual(decision.acceptedAsEvidence, true);
  assert.strictEqual(decision.allowManualEntry, false);
});

// 2. Damaged Drainage
it('2. Damaged drainage returns VALID_CIVIC_ISSUE, accepts into evidence, enables auto-fill', () => {
  const aiResult = {
    decision_outcome: 'VALID_CIVIC_ISSUE',
    decision_message: 'Civic issue verified and accepted.',
    detected: true,
    detected_class: 'blocked_drain',
    category: 'Drainage',
    confidence: 0.85,
    allow_manual: false,
    accepted_as_evidence: true
  };
  const decision = evaluateCivicImageDecision(aiResult, 'Drainage');
  assert.strictEqual(decision.outcome, 'VALID_CIVIC_ISSUE');
  assert.strictEqual(decision.acceptedAsEvidence, true);
  assert.strictEqual(decision.allowManualEntry, false);
});

// 3. Leaking Pipe
it('3. Leaking pipe returns VALID_CIVIC_ISSUE, accepts into evidence, enables auto-fill', () => {
  const aiResult = {
    decision_outcome: 'VALID_CIVIC_ISSUE',
    decision_message: 'Civic issue verified and accepted.',
    detected: true,
    detected_class: 'water_leakage',
    category: 'Water Supply',
    confidence: 0.90,
    allow_manual: false,
    accepted_as_evidence: true
  };
  const decision = evaluateCivicImageDecision(aiResult, 'Water Supply');
  assert.strictEqual(decision.outcome, 'VALID_CIVIC_ISSUE');
  assert.strictEqual(decision.acceptedAsEvidence, true);
  assert.strictEqual(decision.allowManualEntry, false);
});

// 4. Garbage Accumulation
it('4. Garbage accumulation returns VALID_CIVIC_ISSUE, accepts into evidence, enables auto-fill', () => {
  const aiResult = {
    decision_outcome: 'VALID_CIVIC_ISSUE',
    decision_message: 'Civic issue verified and accepted.',
    detected: true,
    detected_class: 'plastic',
    category: 'Sanitation',
    confidence: 0.82,
    allow_manual: false,
    accepted_as_evidence: true
  };
  const decision = evaluateCivicImageDecision(aiResult, 'Sanitation');
  assert.strictEqual(decision.outcome, 'VALID_CIVIC_ISSUE');
  assert.strictEqual(decision.acceptedAsEvidence, true);
  assert.strictEqual(decision.allowManualEntry, false);
});

// 5. Clean Road
it('5. Clean undamaged road returns NO_CIVIC_ISSUE, rejects image, no manual fallback', () => {
  const aiResult = {
    decision_outcome: 'NO_CIVIC_ISSUE',
    decision_message: 'No civic issue found. Please upload an image showing a genuine civic problem.',
    detected: false,
    road_condition: 'clean',
    confidence: 0.92,
    allow_manual: false,
    accepted_as_evidence: false
  };
  const decision = evaluateCivicImageDecision(aiResult, 'Roads');
  assert.strictEqual(decision.outcome, 'NO_CIVIC_ISSUE');
  assert.strictEqual(decision.acceptedAsEvidence, false);
  assert.strictEqual(decision.allowManualEntry, false);
  assert.strictEqual(decision.message, 'No civic issue found. Please upload an image showing a genuine civic problem.');
});

// 6. Normal Functional Drain
it('6. Normal functional drain returns NO_CIVIC_ISSUE, rejects image, no manual fallback', () => {
  const aiResult = {
    decision_outcome: 'NO_CIVIC_ISSUE',
    decision_message: 'No civic issue found. Please upload an image showing a genuine civic problem.',
    detected: false,
    drain_condition: 'normal',
    confidence: 0.95,
    allow_manual: false,
    accepted_as_evidence: false
  };
  const decision = evaluateCivicImageDecision(aiResult, 'Drainage');
  assert.strictEqual(decision.outcome, 'NO_CIVIC_ISSUE');
  assert.strictEqual(decision.acceptedAsEvidence, false);
  assert.strictEqual(decision.allowManualEntry, false);
  assert.strictEqual(decision.message, 'No civic issue found. Please upload an image showing a genuine civic problem.');
});

// 7. Non-civic Animal
it('7. Animal image returns INVALID_IMAGE, rejects image, no manual fallback', () => {
  const aiResult = {
    decision_outcome: 'INVALID_IMAGE',
    decision_message: 'This is not a civic issue. Please upload a valid civic image.',
    detected: false,
    confidence: 0.0,
    allow_manual: false,
    accepted_as_evidence: false
  };
  const decision = evaluateCivicImageDecision(aiResult, 'Roads');
  assert.strictEqual(decision.outcome, 'INVALID_IMAGE');
  assert.strictEqual(decision.acceptedAsEvidence, false);
  assert.strictEqual(decision.allowManualEntry, false);
  assert.strictEqual(decision.message, 'This is not a civic issue. Please upload a valid civic image.');
});

// 8. Ordinary Indoor Tiles
it('8. Ordinary tile texture returns INVALID_IMAGE, rejects image, no manual fallback', () => {
  const aiResult = {
    decision_outcome: 'INVALID_IMAGE',
    decision_message: 'This is not a civic issue. Please upload a valid civic image.',
    detected: false,
    confidence: 0.0,
    allow_manual: false,
    accepted_as_evidence: false
  };
  const decision = evaluateCivicImageDecision(aiResult, 'Roads');
  assert.strictEqual(decision.outcome, 'INVALID_IMAGE');
  assert.strictEqual(decision.acceptedAsEvidence, false);
  assert.strictEqual(decision.allowManualEntry, false);
  assert.strictEqual(decision.message, 'This is not a civic issue. Please upload a valid civic image.');
});

// 9. Unrelated Vehicle
it('9. Unrelated vehicle returns INVALID_IMAGE, rejects image, no manual fallback', () => {
  const aiResult = {
    decision_outcome: 'INVALID_IMAGE',
    decision_message: 'This is not a civic issue. Please upload a valid civic image.',
    detected: false,
    confidence: 0.0,
    allow_manual: false,
    accepted_as_evidence: false
  };
  const decision = evaluateCivicImageDecision(aiResult, 'Roads');
  assert.strictEqual(decision.outcome, 'INVALID_IMAGE');
  assert.strictEqual(decision.acceptedAsEvidence, false);
  assert.strictEqual(decision.allowManualEntry, false);
  assert.strictEqual(decision.message, 'This is not a civic issue. Please upload a valid civic image.');
});

// 10. Random Indoor Room
it('10. Random indoor room returns INVALID_IMAGE, rejects image, no manual fallback', () => {
  const aiResult = {
    decision_outcome: 'INVALID_IMAGE',
    decision_message: 'This is not a civic issue. Please upload a valid civic image.',
    detected: false,
    confidence: 0.0,
    allow_manual: false,
    accepted_as_evidence: false
  };
  const decision = evaluateCivicImageDecision(aiResult, 'Roads');
  assert.strictEqual(decision.outcome, 'INVALID_IMAGE');
  assert.strictEqual(decision.acceptedAsEvidence, false);
  assert.strictEqual(decision.allowManualEntry, false);
  assert.strictEqual(decision.message, 'This is not a civic issue. Please upload a valid civic image.');
});

// 11. Incidental Background Objects with Genuine Defect
it('11. Incidental background pedestrians/vehicles with genuine defect returns VALID_CIVIC_ISSUE', () => {
  const aiResult = {
    decision_outcome: 'VALID_CIVIC_ISSUE',
    decision_message: 'Civic issue verified and accepted.',
    detected: true,
    detected_class: 'Pothole',
    category: 'Roads',
    confidence: 0.75,
    allow_manual: false,
    accepted_as_evidence: true
  };
  const decision = evaluateCivicImageDecision(aiResult, 'Roads');
  assert.strictEqual(decision.outcome, 'VALID_CIVIC_ISSUE');
  assert.strictEqual(decision.acceptedAsEvidence, true);
  assert.strictEqual(decision.allowManualEntry, false);
});

// 12. Uncertain Civic Damage
it('12. Genuine civic infrastructure with uncertain defect returns CIVIC_ISSUE_UNCERTAIN and unlocks manual entry', () => {
  const aiResult = {
    decision_outcome: 'CIVIC_ISSUE_UNCERTAIN',
    decision_message: 'Civic issue detected but classification is uncertain. Manual details enabled for municipal verification.',
    detected: false,
    confidence: 0.30,
    allow_manual: true,
    accepted_as_evidence: true
  };
  const decision = evaluateCivicImageDecision(aiResult, 'Roads');
  assert.strictEqual(decision.outcome, 'CIVIC_ISSUE_UNCERTAIN');
  assert.strictEqual(decision.acceptedAsEvidence, true);
  assert.strictEqual(decision.allowManualEntry, true);
});

console.log(`\nResults: ${passed} / ${total} tests passed.`);
if (passed !== total) {
  process.exit(1);
}

