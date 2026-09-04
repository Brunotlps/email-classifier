const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const projectRoot = path.resolve(__dirname, '..');
let messageListener;

global.chrome = {
    runtime: {
        onMessage: {
            addListener(listener) {
                messageListener = listener;
            },
        },
    },
};

require(path.join(projectRoot, 'extension', 'background.js'));

test('manifest MV3 references the packaged service worker', () => {
    const manifestPath = path.join(projectRoot, 'extension', 'manifest.json');
    const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
    const serviceWorkerPath = path.join(
        projectRoot,
        'extension',
        manifest.background.service_worker,
    );

    assert.equal(manifest.manifest_version, 3);
    assert.equal(manifest.background.service_worker, 'background.js');
    assert.equal(fs.existsSync(serviceWorkerPath), true);
    assert.equal(typeof messageListener, 'function');
});

test('listener ignores unrelated messages', () => {
    assert.equal(messageListener({ type: 'UNRELATED' }, {}, () => {}), false);
});

test('listener keeps the channel open and returns backend data', async () => {
    const analysis = {
        summary: 'Synthetic summary.',
        category: 'Outro',
        priority: 'baixa',
        action_required: false,
        suggestions: [],
    };
    let receivedRequest;

    global.fetch = async (url, options) => {
        receivedRequest = { url, options };
        return { ok: true, json: async () => analysis };
    };

    const response = await new Promise((resolve, reject) => {
        const isAsyncResponse = messageListener(
            {
                type: 'ANALYZE_EMAIL',
                emailText: 'Synthetic email content for extension messaging test.',
                language: 'en',
            },
            {},
            resolve,
        );

        assert.equal(isAsyncResponse, true);
        setTimeout(() => reject(new Error('Listener did not respond')), 1000);
    });

    assert.deepEqual(response, { ok: true, data: analysis });
    assert.equal(receivedRequest.url, 'https://email-classifier-api.fly.dev/api/v1/analyze');
    assert.equal(receivedRequest.options.method, 'POST');
    assert.deepEqual(JSON.parse(receivedRequest.options.body), {
        email_content: 'Synthetic email content for extension messaging test.',
        language: 'en',
    });
});

test('listener turns backend failures into explicit responses', async () => {
    global.fetch = async () => {
        throw new Error('synthetic network failure');
    };

    const response = await new Promise((resolve, reject) => {
        const isAsyncResponse = messageListener(
            {
                type: 'ANALYZE_EMAIL',
                emailText: 'Synthetic email content for failure test.',
                language: 'pt',
            },
            {},
            resolve,
        );

        assert.equal(isAsyncResponse, true);
        setTimeout(() => reject(new Error('Listener did not respond')), 1000);
    });

    assert.deepEqual(response, { ok: false, error: 'synthetic network failure' });
});
