import {describe,it,expect} from 'vitest';
import fixtures from '../../fixtures/countLines011';
import {parseCountLines,normalizeName} from '../../../src/features/video-analysis/countLinesContracts';
describe('011 closed protocol',()=>{
 for(const e of fixtures.valid)it(e.name,()=>expect(()=>parseCountLines(e.schema,e.data)).not.toThrow());
 for(const e of [...fixtures.invalid_shape,...fixtures.invalid_semantic])it('rejects '+e.name,()=>expect(()=>parseCountLines(e.schema,e.data)).toThrow());
 it('counts graphemes rather than UTF16 and normalizes NFC',()=>{expect(normalizeName('  VÍA  CENTRAL ')).toBe('VÍA CENTRAL');expect(()=>normalizeName('👩‍👩‍👧‍👦'.repeat(60))).not.toThrow()});
});
