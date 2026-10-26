import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import { fileURLToPath } from 'node:url'

const ENTRY = fileURLToPath(new URL('../dashboard/dist/index.js', import.meta.url))

function settle() {
  return new Promise(resolve => setImmediate(resolve))
}

test('browser dashboard uses the authenticated web SDK and bridges a fresh WS URL', async () => {
  let component = null
  let view = { html: '', name: '', error: '' }
  let effectRan = false
  let cleanup = null
  const ref = { current: null }
  const frameWindow = { sent: [], postMessage(body, target) { this.sent.push({ body, target }) } }
  const listeners = new Map()
  const calls = []
  const React = {
    createElement(type, props, ...children) {
      if (type === 'iframe' && props && props.ref) props.ref.current = { contentWindow: frameWindow }
      return { type, props: props || {}, children }
    }
  }
  const hooks = {
    useState: () => [view, next => { view = next }],
    useRef: () => ref,
    useEffect(fn) { if (!effectRan) { effectRan = true; cleanup = fn() } }
  }
  const window = {
    __HERMES_PLUGIN_SDK__: {
      sdkVersion: '1.1.0', React, hooks, api: {}, components: {}, utils: {}, useI18n() {},
      fetchJSON: async path => {
        calls.push(['json', path])
        return { settings: { schema_version: 1, profile_id: 'chief-backend' } }
      },
      authedFetch: async path => {
        calls.push(['html', path])
        return { ok: true, text: async () => '<!doctype html><title>sample mirror</title>' }
      },
      buildWsUrl: async path => {
        calls.push(['ws', path])
        return 'wss://dashboard.invalid/api/plugins/hermes-jarvis/events?ticket=sample'
      }
    },
    __HERMES_PLUGINS__: { register: (id, page) => { assert.equal(id, 'hermes-jarvis'); component = page } },
    addEventListener(type, fn) { listeners.set(type, fn) },
    removeEventListener(type, fn) { if (listeners.get(type) === fn) listeners.delete(type) }
  }

  new Function('window', fs.readFileSync(ENTRY, 'utf8'))(window)
  assert.equal(typeof component, 'function')
  let rendered = component()
  assert.equal(rendered.children[0].type, 'div', 'identity is checked before any mirror mounts')
  await settle(); await settle()
  rendered = component()
  const iframe = rendered.children[0]
  assert.equal(iframe.type, 'iframe')
  assert.match(iframe.props.srcDoc, /sample mirror/)
  const boot = JSON.parse(iframe.props.name)
  assert.equal(boot.profileId, 'chief-backend')
  assert.equal(boot.parentWsBridge, true)
  assert.deepEqual(calls.slice(0, 2), [
    ['json', '/api/plugins/hermes-jarvis/state'],
    ['html', '/api/plugins/hermes-jarvis/mirror']
  ])

  listeners.get('message')({
    source: frameWindow,
    data: { type: 'hermes-jarvis:ws-url-request', bridgeId: boot.bridgeId, requestId: '7' }
  })
  await settle()
  assert.deepEqual(calls.at(-1), ['ws', '/api/plugins/hermes-jarvis/events'])
  assert.equal(frameWindow.sent.length, 1)
  assert.equal(frameWindow.sent[0].body.requestId, '7')
  assert.match(frameWindow.sent[0].body.url, /ticket=sample/)

  cleanup()
  assert.equal(listeners.has('message'), false)
})

test('browser dashboard fails closed when authenticated state has no profile identity', async () => {
  let component = null
  let view = { html: '', name: '', error: '' }
  let effectRan = false
  let htmlReads = 0
  const React = { createElement: (type, props, ...children) => ({ type, props: props || {}, children }) }
  const window = {
    __HERMES_PLUGIN_SDK__: {
      React,
      hooks: {
        useState: () => [view, next => { view = next }],
        useRef: () => ({ current: null }),
        useEffect(fn) { if (!effectRan) { effectRan = true; fn() } }
      },
      fetchJSON: async () => ({ settings: null }),
      authedFetch: async () => { htmlReads += 1; return { ok: true, text: async () => 'private' } },
      buildWsUrl: async () => 'wss://unused.invalid'
    },
    __HERMES_PLUGINS__: { register: (id, page) => { component = page } },
    addEventListener() {}, removeEventListener() {}
  }
  new Function('window', fs.readFileSync(ENTRY, 'utf8'))(window)
  component()
  await settle(); await settle()
  const rendered = component()
  assert.equal(rendered.children[0].type, 'div')
  assert.match(rendered.children[0].children[0], /Connect to this chief profile dashboard/)
  assert.equal(htmlReads, 0, 'mirror HTML is not fetched before profile identity binds')
})
