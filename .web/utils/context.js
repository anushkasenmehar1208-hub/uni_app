import { createContext, useContext, useMemo, useReducer, useState, createElement, useEffect } from "react"
import { applyDelta, ReflexEvent, hydrateClientStorage, useEventLoop, refs } from "$/utils/state"
import { jsx } from "@emotion/react";

export const initialState = {"reflex___state____state": {"is_hydrated_rx_state_": false, "router_rx_state_": {"session": {"client_token": "", "client_ip": "", "session_id": ""}, "headers": {"host": "", "origin": "", "upgrade": "", "connection": "", "cookie": "", "pragma": "", "cache_control": "", "user_agent": "", "sec_websocket_version": "", "sec_websocket_key": "", "sec_websocket_extensions": "", "accept_encoding": "", "accept_language": "", "raw_headers": {}}, "page": {"host": "", "path": "", "raw_path": "", "full_path": "", "full_raw_path": "", "params": {}}, "url": "", "route_id": ""}}, "reflex___state____state.reflex___state____frontend_event_exception_state": {}, "reflex___state____state.reflex___state____on_load_internal_state": {}, "reflex___state____state.reflex___state____update_vars_internal_state": {}, "reflex___state____state.reflex_local_auth___local_auth____local_auth_state": {"auth_token_rx_state_": "", "authenticated_user_rx_state_": {"id": -1, "enabled": false}, "is_authenticated_rx_state_": false}, "reflex___state____state.reflex_local_auth___local_auth____local_auth_state.reflex_local_auth___login____login_state": {"error_message_rx_state_": "", "redirect_to_rx_state_": ""}, "reflex___state____state.reflex_local_auth___local_auth____local_auth_state.reflex_local_auth___registration____registration_state": {"error_message_rx_state_": "", "new_user_id_rx_state_": -1, "success_rx_state_": false}, "reflex___state____state.reflex_local_auth___local_auth____local_auth_state.uni_app___uni_app____app_state": {"GLOBAL_MEMORY_TRIGGER_NEW_MSGS_rx_state_": 24, "PAST_HITS_LIMIT_rx_state_": 8, "PAST_HITS_MAX_CHARS_rx_state_": 220, "SCOPE_SUMMARY_TRIGGER_NEW_MSGS_rx_state_": 12, "active_model_name_rx_state_": "llama-3.3-70b-versatile", "active_scope_rx_state_": "home", "available_semesters_rx_state_": [], "can_send_message_rx_state_": true, "chat_history_rx_state_": [], "chat_input_rx_state_": "", "current_day_rx_state_": 1, "current_session_choice_rx_state_": "", "current_session_id_rx_state_": "", "current_topic_index_rx_state_": 0, "daily_message_count_rx_state_": 0, "days_since_registration_rx_state_": 999, "degree_rx_state_": "", "is_empty_chat_rx_state_": true, "is_generating_plan_rx_state_": false, "is_in_trial_rx_state_": false, "is_premium_1_rx_state_": false, "is_premium_2_rx_state_": false, "is_processing_rx_state_": false, "is_started_rx_state_": false, "last_message_date_rx_state_": "", "memory_summary_rx_state_": "", "messages_left_today_rx_state_": 5, "name_rx_state_": "", "options_rx_state_": ["Software Engineering"], "payment_error_rx_state_": "", "payment_processing_rx_state_": false, "profile_created_at_rx_state_": "", "selected_semester_rx_state_": "", "selected_year_rx_state_": "", "semester_short_label_rx_state_": ":", "sessions_rx_state_": [], "show_pricing_modal_rx_state_": false, "status_text_rx_state_": "", "step_rx_state_": 0, "streak_rx_state_": 1, "tier_label_rx_state_": "🔒 Free", "today_plan_rx_state_": "", "trial_days_left_rx_state_": 0, "view_mode_rx_state_": "home"}}

export const defaultColorMode = "system"
export const ColorModeContext = createContext(null);
export const UploadFilesContext = createContext(null);
export const DispatchContext = createContext(null);
export const StateContexts = {reflex___state____state: createContext(null),reflex___state____state__reflex___state____frontend_event_exception_state: createContext(null),reflex___state____state__reflex___state____on_load_internal_state: createContext(null),reflex___state____state__reflex___state____update_vars_internal_state: createContext(null),reflex___state____state__reflex_local_auth___local_auth____local_auth_state: createContext(null),reflex___state____state__reflex_local_auth___local_auth____local_auth_state__reflex_local_auth___login____login_state: createContext(null),reflex___state____state__reflex_local_auth___local_auth____local_auth_state__reflex_local_auth___registration____registration_state: createContext(null),reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state: createContext(null),};
export const EventLoopContext = createContext(null);
export const clientStorage = {"cookies": {}, "local_storage": {"reflex___state____state.reflex_local_auth___local_auth____local_auth_state.auth_token_rx_state_": {"name": "_auth_token", "sync": false}}, "session_storage": {}}


export const state_name = "reflex___state____state"

export const exception_state_name = "reflex___state____state.reflex___state____frontend_event_exception_state"

// These events are triggered on initial load and each page navigation.
export const onLoadInternalEvent = () => {
    const internal_events = [];

    // Get tracked cookie and local storage vars to send to the backend.
    const client_storage_vars = hydrateClientStorage(clientStorage);
    // But only send the vars if any are actually set in the browser.
    if (client_storage_vars && Object.keys(client_storage_vars).length !== 0) {
        internal_events.push(
            ReflexEvent(
                'reflex___state____state.reflex___state____update_vars_internal_state.update_vars_internal',
                {vars: client_storage_vars},
            ),
        );
    }

    // `on_load_internal` triggers the correct on_load event(s) for the current page.
    // If the page does not define any on_load event, this will just set `is_hydrated = true`.
    internal_events.push(ReflexEvent('reflex___state____state.reflex___state____on_load_internal_state.on_load_internal'));

    return internal_events;
}

// The following events are sent when the websocket connects or reconnects.
export const initialEvents = () => [
    ReflexEvent('reflex___state____state.hydrate'),
    ...onLoadInternalEvent()
]
    

export const isDevMode = true;

export function UploadFilesProvider({ children }) {
  const [filesById, setFilesById] = useState({})
  refs["__clear_selected_files"] = (id) => setFilesById(filesById => {
    const newFilesById = {...filesById}
    delete newFilesById[id]
    return newFilesById
  })
  return createElement(
    UploadFilesContext.Provider,
    { value: [filesById, setFilesById] },
    children
  );
}

export function ClientSide(component) {
  return ({ children, ...props }) => {
    const [Component, setComponent] = useState(null);
    useEffect(() => {
      async function load() {
        const comp = await component();
        setComponent(() => comp);
      }
      load();
    }, []);
    return Component ? jsx(Component, props, children) : null;
  };
}

export function EventLoopProvider({ children }) {
  const dispatch = useContext(DispatchContext)
  const [addEvents, connectErrors] = useEventLoop(
    dispatch,
    initialEvents,
    clientStorage,
  )
  return createElement(
    EventLoopContext.Provider,
    { value: [addEvents, connectErrors] },
    children
  );
}

export function StateProvider({ children }) {
  const [reflex___state____state, dispatch_reflex___state____state] = useReducer(applyDelta, initialState["reflex___state____state"])
const [reflex___state____state__reflex___state____frontend_event_exception_state, dispatch_reflex___state____state__reflex___state____frontend_event_exception_state] = useReducer(applyDelta, initialState["reflex___state____state.reflex___state____frontend_event_exception_state"])
const [reflex___state____state__reflex___state____on_load_internal_state, dispatch_reflex___state____state__reflex___state____on_load_internal_state] = useReducer(applyDelta, initialState["reflex___state____state.reflex___state____on_load_internal_state"])
const [reflex___state____state__reflex___state____update_vars_internal_state, dispatch_reflex___state____state__reflex___state____update_vars_internal_state] = useReducer(applyDelta, initialState["reflex___state____state.reflex___state____update_vars_internal_state"])
const [reflex___state____state__reflex_local_auth___local_auth____local_auth_state, dispatch_reflex___state____state__reflex_local_auth___local_auth____local_auth_state] = useReducer(applyDelta, initialState["reflex___state____state.reflex_local_auth___local_auth____local_auth_state"])
const [reflex___state____state__reflex_local_auth___local_auth____local_auth_state__reflex_local_auth___login____login_state, dispatch_reflex___state____state__reflex_local_auth___local_auth____local_auth_state__reflex_local_auth___login____login_state] = useReducer(applyDelta, initialState["reflex___state____state.reflex_local_auth___local_auth____local_auth_state.reflex_local_auth___login____login_state"])
const [reflex___state____state__reflex_local_auth___local_auth____local_auth_state__reflex_local_auth___registration____registration_state, dispatch_reflex___state____state__reflex_local_auth___local_auth____local_auth_state__reflex_local_auth___registration____registration_state] = useReducer(applyDelta, initialState["reflex___state____state.reflex_local_auth___local_auth____local_auth_state.reflex_local_auth___registration____registration_state"])
const [reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state, dispatch_reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state] = useReducer(applyDelta, initialState["reflex___state____state.reflex_local_auth___local_auth____local_auth_state.uni_app___uni_app____app_state"])
  const dispatchers = useMemo(() => {
    return {
      "reflex___state____state": dispatch_reflex___state____state,
"reflex___state____state.reflex___state____frontend_event_exception_state": dispatch_reflex___state____state__reflex___state____frontend_event_exception_state,
"reflex___state____state.reflex___state____on_load_internal_state": dispatch_reflex___state____state__reflex___state____on_load_internal_state,
"reflex___state____state.reflex___state____update_vars_internal_state": dispatch_reflex___state____state__reflex___state____update_vars_internal_state,
"reflex___state____state.reflex_local_auth___local_auth____local_auth_state": dispatch_reflex___state____state__reflex_local_auth___local_auth____local_auth_state,
"reflex___state____state.reflex_local_auth___local_auth____local_auth_state.reflex_local_auth___login____login_state": dispatch_reflex___state____state__reflex_local_auth___local_auth____local_auth_state__reflex_local_auth___login____login_state,
"reflex___state____state.reflex_local_auth___local_auth____local_auth_state.reflex_local_auth___registration____registration_state": dispatch_reflex___state____state__reflex_local_auth___local_auth____local_auth_state__reflex_local_auth___registration____registration_state,
"reflex___state____state.reflex_local_auth___local_auth____local_auth_state.uni_app___uni_app____app_state": dispatch_reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state,
    }
  }, [])

  return (
    createElement(StateContexts.reflex___state____state,{value: reflex___state____state},
createElement(StateContexts.reflex___state____state__reflex___state____frontend_event_exception_state,{value: reflex___state____state__reflex___state____frontend_event_exception_state},
createElement(StateContexts.reflex___state____state__reflex___state____on_load_internal_state,{value: reflex___state____state__reflex___state____on_load_internal_state},
createElement(StateContexts.reflex___state____state__reflex___state____update_vars_internal_state,{value: reflex___state____state__reflex___state____update_vars_internal_state},
createElement(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state,{value: reflex___state____state__reflex_local_auth___local_auth____local_auth_state},
createElement(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__reflex_local_auth___login____login_state,{value: reflex___state____state__reflex_local_auth___local_auth____local_auth_state__reflex_local_auth___login____login_state},
createElement(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__reflex_local_auth___registration____registration_state,{value: reflex___state____state__reflex_local_auth___local_auth____local_auth_state__reflex_local_auth___registration____registration_state},
createElement(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state,{value: reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state},
    createElement(DispatchContext, {value: dispatchers}, children)
    ))))))))
  )
}