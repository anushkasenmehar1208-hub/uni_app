import {Fragment,useCallback,useContext,useEffect,useRef} from "react"
import {ColorModeContext,EventLoopContext,StateContexts} from "$/utils/context"
import {ReflexEvent,isTrue,refs} from "$/utils/state"
import {Badge as RadixThemesBadge,Box as RadixThemesBox,Button as RadixThemesButton,Callout as RadixThemesCallout,Code as RadixThemesCode,Flex as RadixThemesFlex,Heading as RadixThemesHeading,IconButton as RadixThemesIconButton,Link as RadixThemesLink,Select as RadixThemesSelect,Separator as RadixThemesSeparator,Spinner as RadixThemesSpinner,Text as RadixThemesText,TextArea as RadixThemesTextArea,TextField as RadixThemesTextField} from "@radix-ui/themes"
import {ArrowUp as LucideArrowUp,Info as LucideInfo,Trash2 as LucideTrash2} from "lucide-react"
import DebounceInput from "react-debounce-input"
import {Helmet} from "react-helmet"
import ReactMarkdown from "react-markdown"
import remarkMath from "remark-math"
import remarkGfm from "remark-gfm"
import rehypeKatex from "rehype-katex"
import "katex/dist/katex.min.css"
import rehypeRaw from "rehype-raw"
import rehypeUnwrapImages from "rehype-unwrap-images"
import {Link as ReactRouterLink} from "react-router"
import {PrismAsyncLight as SyntaxHighlighter} from "react-syntax-highlighter"
import oneLight from "react-syntax-highlighter/dist/esm/styles/prism/one-light"
import oneDark from "react-syntax-highlighter/dist/esm/styles/prism/one-dark"
import {jsx} from "@emotion/react"




function Text_de6457553040f2445b96779a74733a8a () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(RadixThemesText,{as:"p",css:({ ["color"] : "white" })},reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.name_rx_state_)
  )
}


function Text_3a59335c13efa3792704b92daa5ff0f5 () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(RadixThemesText,{as:"p",css:({ ["color"] : "rgba(0,255,136,0.7)", ["fontSize"] : "0.85rem", ["fontWeight"] : "bold", ["letterSpacing"] : "1px" })},("Lets study "+reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.degree_rx_state_))
  )
}


function Text_8c52ca47f1fbef0fa724c97bdf85532e () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(RadixThemesText,{as:"p"},reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.streak_rx_state_)
  )
}


function Button_439d97f8c460f4e9420e6abf6128efec () {
  const [addEvents, connectErrors] = useContext(EventLoopContext);

const on_click_90cddb28e72cfa4144bda5e7f0ed8d18 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.reflex_local_auth___local_auth____local_auth_state.uni_app___uni_app____app_state.new_chat", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])

  return (
    jsx(RadixThemesButton,{color:"green",onClick:on_click_90cddb28e72cfa4144bda5e7f0ed8d18,variant:"outline"},"New chat")
  )
}


function Button_7e24b63790dbafb0c037bec8fa2966f7 () {
  const [addEvents, connectErrors] = useContext(EventLoopContext);

const on_click_9ad88d0d8cac89d7a6714dbdacc2b512 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.reflex_local_auth___local_auth____local_auth_state.uni_app___uni_app____app_state.logout", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])

  return (
    jsx(RadixThemesButton,{color:"green",onClick:on_click_9ad88d0d8cac89d7a6714dbdacc2b512,variant:"outline"},"Logout")
  )
}


function Callout__text_5e8c48c2a816ffde8fa43a30b08b9d40 () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(RadixThemesCallout.Text,{},reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.status_text_rx_state_)
  )
}


function Fragment_76171a76cc42899e898bf7ebf601bc5c () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(Fragment,{},(!((reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.status_text_rx_state_?.valueOf?.() === ""?.valueOf?.()))?(jsx(Fragment,{},jsx(RadixThemesCallout.Root,{color:"yellow",css:({ ["icon"] : "info", ["width"] : "100%" })},jsx(RadixThemesCallout.Icon,{},jsx(LucideInfo,{},)),jsx(Callout__text_5e8c48c2a816ffde8fa43a30b08b9d40,{},)))):(jsx(Fragment,{},))))
  )
}


function Button_14716ed103369a897d85960a6ca52a8e () {
  const [addEvents, connectErrors] = useContext(EventLoopContext);

const on_click_b340546bd22adcb19e424cad0026dd65 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.reflex_local_auth___local_auth____local_auth_state.uni_app___uni_app____app_state.set_year", ({ ["year"] : "Year 1" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])

  return (
    jsx(RadixThemesButton,{color:"green",css:({ ["border"] : "1px solid #00ff88", ["boxShadow"] : "0 0 10px rgba(0,255,136,0.2)", ["textTransform"] : "uppercase", ["fontWeight"] : "bold", ["letterSpacing"] : "1px", ["transition"] : "all 0.3s ease", ["&:hover"] : ({ ["boxShadow"] : "0 0 25px rgba(0,255,136,0.6)", ["transform"] : "translateX(10px)", ["background"] : "rgba(0,255,136,0.1)" }), ["width"] : "100%", ["height"] : "60px" }),onClick:on_click_b340546bd22adcb19e424cad0026dd65,variant:"outline"},"FIRST YEAR")
  )
}


function Button_01b17aef5561a36e54d719a3e4413862 () {
  const [addEvents, connectErrors] = useContext(EventLoopContext);

const on_click_d1357d6a06a985a7fd035490e07232be = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.reflex_local_auth___local_auth____local_auth_state.uni_app___uni_app____app_state.set_year", ({ ["year"] : "Year 2" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])

  return (
    jsx(RadixThemesButton,{color:"green",css:({ ["border"] : "1px solid #00ff88", ["boxShadow"] : "0 0 10px rgba(0,255,136,0.2)", ["textTransform"] : "uppercase", ["fontWeight"] : "bold", ["letterSpacing"] : "1px", ["transition"] : "all 0.3s ease", ["&:hover"] : ({ ["boxShadow"] : "0 0 25px rgba(0,255,136,0.6)", ["transform"] : "translateX(10px)", ["background"] : "rgba(0,255,136,0.1)" }), ["width"] : "100%", ["height"] : "60px" }),onClick:on_click_d1357d6a06a985a7fd035490e07232be,variant:"outline"},"SECOND YEAR")
  )
}


function Button_d10f6b97a164049b66b4340b87283f43 () {
  const [addEvents, connectErrors] = useContext(EventLoopContext);

const on_click_8a05bc83fdf56a3c3ab80b6dfa7b355b = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.reflex_local_auth___local_auth____local_auth_state.uni_app___uni_app____app_state.set_year", ({ ["year"] : "Year 3" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])

  return (
    jsx(RadixThemesButton,{color:"green",css:({ ["border"] : "1px solid #00ff88", ["boxShadow"] : "0 0 10px rgba(0,255,136,0.2)", ["textTransform"] : "uppercase", ["fontWeight"] : "bold", ["letterSpacing"] : "1px", ["transition"] : "all 0.3s ease", ["&:hover"] : ({ ["boxShadow"] : "0 0 25px rgba(0,255,136,0.6)", ["transform"] : "translateX(10px)", ["background"] : "rgba(0,255,136,0.1)" }), ["width"] : "100%", ["height"] : "60px" }),onClick:on_click_8a05bc83fdf56a3c3ab80b6dfa7b355b,variant:"outline"},"THIRD YEAR")
  )
}


function Button_8d06214346bc6d7e63bd034dd3510e32 () {
  const [addEvents, connectErrors] = useContext(EventLoopContext);

const on_click_e0ca99cd3fd53d74ab6e287502539240 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.reflex_local_auth___local_auth____local_auth_state.uni_app___uni_app____app_state.set_year", ({ ["year"] : "Year 4" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])

  return (
    jsx(RadixThemesButton,{color:"green",css:({ ["border"] : "1px solid #00ff88", ["boxShadow"] : "0 0 10px rgba(0,255,136,0.2)", ["textTransform"] : "uppercase", ["fontWeight"] : "bold", ["letterSpacing"] : "1px", ["transition"] : "all 0.3s ease", ["&:hover"] : ({ ["boxShadow"] : "0 0 25px rgba(0,255,136,0.6)", ["transform"] : "translateX(10px)", ["background"] : "rgba(0,255,136,0.1)" }), ["width"] : "100%", ["height"] : "60px" }),onClick:on_click_e0ca99cd3fd53d74ab6e287502539240,variant:"outline"},"FOURTH YEAR")
  )
}


function Button_1e1720c42c6c49be253a3a9db0b04083 () {
  const [addEvents, connectErrors] = useContext(EventLoopContext);

const on_click_10379475ea31d72c027462fced3f5d94 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.reflex_local_auth___local_auth____local_auth_state.uni_app___uni_app____app_state.back_to_years", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])

  return (
    jsx(RadixThemesButton,{color:"green",css:({ ["width"] : "100%" }),onClick:on_click_10379475ea31d72c027462fced3f5d94,variant:"outline"},"Back")
  )
}


function Text_ee51ba383f8e2c6b3e0652d39825779f () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(RadixThemesText,{as:"p",css:({ ["color"] : "white", ["fontWeight"] : "bold" })},reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.selected_year_rx_state_)
  )
}


function Flex_a72385e958ca19bc2b8e56f171b4f03c () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)
const [addEvents, connectErrors] = useContext(EventLoopContext);



  return (
    jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["width"] : "100%" }),direction:"column",gap:"3"},jsx(Button_1e1720c42c6c49be253a3a9db0b04083,{},),jsx(Text_ee51ba383f8e2c6b3e0652d39825779f,{},),Array.prototype.map.call(reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.available_semesters_rx_state_ ?? [],((sem_rx_state_,index_e90abb3aea6e3870b0de0212bd3764c2)=>(jsx(RadixThemesButton,{color:"green",css:({ ["border"] : "1px solid #00ff88", ["boxShadow"] : "0 0 10px rgba(0,255,136,0.2)", ["textTransform"] : "uppercase", ["fontWeight"] : "bold", ["letterSpacing"] : "1px", ["transition"] : "all 0.3s ease", ["&:hover"] : ({ ["boxShadow"] : "0 0 25px rgba(0,255,136,0.6)", ["transform"] : "translateX(10px)", ["background"] : "rgba(0,255,136,0.1)" }), ["width"] : "100%", ["height"] : "60px" }),key:index_e90abb3aea6e3870b0de0212bd3764c2,onClick:((_e) => (addEvents([(ReflexEvent("reflex___state____state.reflex_local_auth___local_auth____local_auth_state.uni_app___uni_app____app_state.open_semester", ({ ["semester"] : sem_rx_state_ }), ({  })))], [_e], ({  })))),variant:"outline"},sem_rx_state_.toUpperCase())))))
  )
}


function Fragment_e7c2f63737b72a5f03ff48c76165e43f () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(Fragment,{},((reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.selected_year_rx_state_?.valueOf?.() === ""?.valueOf?.())?(jsx(Fragment,{},jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["width"] : "100%" }),direction:"column",gap:"3"},jsx(Button_14716ed103369a897d85960a6ca52a8e,{},),jsx(Button_01b17aef5561a36e54d719a3e4413862,{},),jsx(Button_d10f6b97a164049b66b4340b87283f43,{},),jsx(Button_8d06214346bc6d7e63bd034dd3510e32,{},)))):(jsx(Fragment,{},jsx(Flex_a72385e958ca19bc2b8e56f171b4f03c,{},)))))
  )
}


function Box_65affcb847563a74d6e19fc17034b30d () {
  const [addEvents, connectErrors] = useContext(EventLoopContext);

const on_click_e0965ddb639bd8204affb7858dab4b9a = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.reflex_local_auth___local_auth____local_auth_state.uni_app___uni_app____app_state.open_pricing_modal", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])

  return (
    jsx(RadixThemesBox,{css:({ ["background"] : "linear-gradient(135deg,#7c3aed,#a855f7)", ["boxShadow"] : "0 0 20px rgba(168,85,247,0.35)", ["transition"] : "all 0.2s ease", ["&:hover"] : ({ ["filter"] : "brightness(1.1)", ["transform"] : "translateY(-1px)" }), ["width"] : "100%", ["padding"] : "12px 16px", ["borderRadius"] : "14px", ["cursor"] : "pointer" }),onClick:on_click_e0965ddb639bd8204affb7858dab4b9a},jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["alignItems"] : "center", ["width"] : "100%" }),direction:"column",gap:"1"},jsx(RadixThemesText,{as:"p",css:({ ["fontWeight"] : "800", ["fontSize"] : "0.95rem", ["color"] : "white", ["textAlign"] : "center" })},"\ud83d\udc51 Premium Pro"),jsx(RadixThemesText,{as:"p",css:({ ["color"] : "rgba(255,255,255,0.45)", ["fontSize"] : "0.72rem", ["textAlign"] : "center" })},"You're on the Pro plan")))
  )
}


function Box_31dce68e5157af7745f6077db9172192 () {
  const [addEvents, connectErrors] = useContext(EventLoopContext);

const on_click_e0965ddb639bd8204affb7858dab4b9a = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.reflex_local_auth___local_auth____local_auth_state.uni_app___uni_app____app_state.open_pricing_modal", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])

  return (
    jsx(RadixThemesBox,{css:({ ["background"] : "linear-gradient(135deg,#111111 0%,#2a2a2a 50%,#1a1a1a 100%)", ["transition"] : "all 0.2s ease", ["&:hover"] : ({ ["filter"] : "brightness(1.2)", ["transform"] : "translateY(-1px)" }), ["width"] : "100%", ["padding"] : "12px 16px", ["borderRadius"] : "14px", ["cursor"] : "pointer" }),onClick:on_click_e0965ddb639bd8204affb7858dab4b9a},jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["alignItems"] : "center", ["width"] : "100%" }),direction:"column",gap:"1"},jsx(RadixThemesText,{as:"p",css:({ ["textShadow"] : "0 1px 4px rgba(0,0,0,0.6)", ["fontWeight"] : "800", ["fontSize"] : "0.95rem", ["color"] : "white", ["textAlign"] : "center" })},"\u26a1 Premium Fast"),jsx(RadixThemesText,{as:"p",css:({ ["color"] : "rgba(255,255,255,0.45)", ["fontSize"] : "0.72rem", ["textAlign"] : "center" })},"Active plan")))
  )
}


function Text_030b2692a93e2c7be73bec180b28166e () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(RadixThemesText,{as:"p",css:({ ["color"] : "rgba(255,255,255,0.55)", ["fontSize"] : "0.72rem", ["textAlign"] : "center" })},(("Trial \u00b7 "+(JSON.stringify(reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.trial_days_left_rx_state_)))+" days left"))
  )
}


function Box_afef6c45c8f2610d493c788ea8ea7665 () {
  const [addEvents, connectErrors] = useContext(EventLoopContext);

const on_click_e0965ddb639bd8204affb7858dab4b9a = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.reflex_local_auth___local_auth____local_auth_state.uni_app___uni_app____app_state.open_pricing_modal", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])

  return (
    jsx(RadixThemesBox,{css:({ ["background"] : "linear-gradient(135deg,#111111 0%,#2a2a2a 50%,#1a1a1a 100%)", ["transition"] : "all 0.2s ease", ["&:hover"] : ({ ["filter"] : "brightness(1.2)", ["transform"] : "translateY(-1px)" }), ["width"] : "100%", ["padding"] : "12px 16px", ["borderRadius"] : "14px", ["cursor"] : "pointer" }),onClick:on_click_e0965ddb639bd8204affb7858dab4b9a},jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["alignItems"] : "center", ["width"] : "100%" }),direction:"column",gap:"1"},jsx(RadixThemesText,{as:"p",css:({ ["textShadow"] : "0 1px 4px rgba(0,0,0,0.6)", ["fontWeight"] : "800", ["fontSize"] : "0.95rem", ["color"] : "white", ["textAlign"] : "center" })},"\u26a1 Premium Fast"),jsx(Text_030b2692a93e2c7be73bec180b28166e,{},)))
  )
}


function Button_b0823a1b9b250cde5fbc688dbe7333a9 () {
  const [addEvents, connectErrors] = useContext(EventLoopContext);

const on_click_e0965ddb639bd8204affb7858dab4b9a = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.reflex_local_auth___local_auth____local_auth_state.uni_app___uni_app____app_state.open_pricing_modal", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])

  return (
    jsx(RadixThemesButton,{css:({ ["background"] : "linear-gradient(135deg,#0d0d0d 0%,#252525 50%,#1a1a1a 100%)", ["border"] : "none", ["cursor"] : "pointer", ["boxShadow"] : "0 4px 24px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.06)", ["transition"] : "all 0.25s ease", ["&:hover"] : ({ ["boxShadow"] : "0 6px 28px rgba(255,255,255,0.1)", ["transform"] : "translateY(-2px)", ["filter"] : "brightness(1.2)" }), ["&:active"] : ({ ["transform"] : "translateY(0)" }), ["width"] : "100%", ["height"] : "52px", ["borderRadius"] : "14px" }),onClick:on_click_e0965ddb639bd8204affb7858dab4b9a},jsx(RadixThemesText,{as:"p",css:({ ["textShadow"] : "0 1px 4px rgba(0,0,0,0.6)", ["fontWeight"] : "700", ["fontSize"] : "0.88rem", ["color"] : "white" })},"Upgrade to Premium"))
  )
}


function Fragment_7bf9c99e71bab1bfcf473e0f93e6ca4f () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(Fragment,{},(reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.is_in_trial_rx_state_?(jsx(Fragment,{},jsx(Box_afef6c45c8f2610d493c788ea8ea7665,{},))):(jsx(Fragment,{},jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["alignItems"] : "center", ["width"] : "100%" }),direction:"column",gap:"2"},jsx(Button_b0823a1b9b250cde5fbc688dbe7333a9,{},),jsx(RadixThemesText,{as:"p",css:({ ["color"] : "rgba(255,255,255,0.3)", ["fontSize"] : "0.68rem", ["textAlign"] : "center" })},"Unlock unlimited access"))))))
  )
}


function Fragment_44b638a4613babfff5b2c1560999498c () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(Fragment,{},(reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.is_premium_1_rx_state_?(jsx(Fragment,{},jsx(Box_31dce68e5157af7745f6077db9172192,{},))):(jsx(Fragment_7bf9c99e71bab1bfcf473e0f93e6ca4f,{},))))
  )
}


function Fragment_6e5f194f68861ca536a3dffa5fd809b4 () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(Fragment,{},(reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.is_premium_2_rx_state_?(jsx(Fragment,{},jsx(Box_65affcb847563a74d6e19fc17034b30d,{},))):(jsx(Fragment_44b638a4613babfff5b2c1560999498c,{},))))
  )
}


function Flex_8a4bb67a523bd4bf4fc86db456f6d671 () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)
const [addEvents, connectErrors] = useContext(EventLoopContext);



  return (
    jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["width"] : "100%", ["alignItems"] : "stretch", ["maxHeight"] : "200px", ["overflowY"] : "auto" }),direction:"column",gap:"1"},Array.prototype.map.call(reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.sessions_rx_state_ ?? [],((s_rx_state_,index_9ee61a1161d67c4674b90ed950bd9ea8)=>(jsx(RadixThemesFlex,{align:"center",className:"rx-Stack",css:({ ["width"] : "100%" }),direction:"row",key:index_9ee61a1161d67c4674b90ed950bd9ea8,gap:"1"},jsx(RadixThemesButton,{css:({ ["color"] : ((reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.current_session_id_rx_state_?.valueOf?.() === s_rx_state_?.["id"]?.valueOf?.()) ? "#00ff88" : "white"), ["fontWeight"] : ((reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.current_session_id_rx_state_?.valueOf?.() === s_rx_state_?.["id"]?.valueOf?.()) ? "bold" : "normal"), ["textAlign"] : "left", ["justifyContent"] : "flex-start", ["flex"] : "1", ["overflow"] : "hidden", ["textOverflow"] : "ellipsis", ["whiteSpace"] : "nowrap" }),onClick:((_e) => (addEvents([(ReflexEvent("reflex___state____state.reflex_local_auth___local_auth____local_auth_state.uni_app___uni_app____app_state.switch_chat", ({ ["session_id"] : s_rx_state_?.["id"] }), ({  })))], [_e], ({  })))),size:"1",variant:"ghost"},s_rx_state_?.["title"]),jsx(RadixThemesIconButton,{color:"red",css:({ ["padding"] : "6px", ["opacity"] : "0.5", ["&:hover"] : ({ ["opacity"] : "1" }) }),onClick:((_e) => (addEvents([(ReflexEvent("reflex___state____state.reflex_local_auth___local_auth____local_auth_state.uni_app___uni_app____app_state.delete_session", ({ ["session_id"] : s_rx_state_?.["id"] }), ({  })))], [_e], ({  })))),size:"1",variant:"ghost"},jsx(LucideTrash2,{size:12},)))))))
  )
}


function Debounceinput_7f575e319ae587e4b20f9807e50f58c0 () {
  const ref_chat_input = useRef(null); refs["ref_chat_input"] = ref_chat_input;
const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)
const [addEvents, connectErrors] = useContext(EventLoopContext);

const on_change_277b3d0b191b65d16bf5dcc6d016aa8f = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.reflex_local_auth___local_auth____local_auth_state.uni_app___uni_app____app_state.set_chat_input", ({ ["value"] : _e?.["target"]?.["value"] }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])

  return (
    jsx(DebounceInput,{css:({ ["&:placeholder"] : ({ ["color"] : "rgba(255,255,255,0.3)" }), ["&:focus"] : ({ ["borderColor"] : "rgba(0,255,136,0.55)", ["boxShadow"] : "0 0 0 2px rgba(0,255,136,0.12)", ["outline"] : "none" }), ["background"] : "rgba(30,30,35,0.85)", ["border"] : "1px solid rgba(0,255,136,0.25)", ["color"] : "white", ["flex"] : "1", ["minHeight"] : "52px", ["maxHeight"] : "140px", ["borderRadius"] : "14px", ["padding"] : "14px 16px", ["fontSize"] : "0.95rem" }),debounceTimeout:300,element:RadixThemesTextArea,id:"chat_input",inputRef:ref_chat_input,onChange:on_change_277b3d0b191b65d16bf5dcc6d016aa8f,placeholder:"Ask Alex AI anything...",resize:"none",value:reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.chat_input_rx_state_},)
  )
}


function Fragment_02ceb33650e3443dd9f652297025ab5e () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(Fragment,{},(reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.is_processing_rx_state_?(jsx(Fragment,{},jsx(RadixThemesSpinner,{css:({ ["color"] : "white" }),size:"1"},))):(jsx(Fragment,{},jsx(LucideArrowUp,{css:({ ["color"] : "white" }),size:18},)))))
  )
}


function Button_3dd99ab7326b698165a0e71d0e0a9aac () {
  const ref_chat_send_btn = useRef(null); refs["ref_chat_send_btn"] = ref_chat_send_btn;
const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)
const [addEvents, connectErrors] = useContext(EventLoopContext);

const on_click_9c9065621237fc6692a81c9b38fcf94f = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.reflex_local_auth___local_auth____local_auth_state.uni_app___uni_app____app_state.send_message", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])

  return (
    jsx(RadixThemesButton,{css:({ ["background"] : (reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.is_processing_rx_state_ ? "rgba(0,255,136,0.3)" : "rgba(0,255,136,0.85)"), ["border"] : "none", ["cursor"] : "pointer", ["transition"] : "all 0.2s ease", ["flexShrink"] : "0", ["&:hover"] : ({ ["background"] : "#00ff88", ["boxShadow"] : "0 0 16px rgba(0,255,136,0.5)" }), ["isDisabled"] : reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.is_processing_rx_state_, ["borderRadius"] : "12px", ["width"] : "52px", ["height"] : "52px" }),id:"chat_send_btn",onClick:on_click_9c9065621237fc6692a81c9b38fcf94f,ref:ref_chat_send_btn},jsx(Fragment_02ceb33650e3443dd9f652297025ab5e,{},))
  )
}


function Button_48d61029118e4d0217ca909d5e2645b2 () {
  const [addEvents, connectErrors] = useContext(EventLoopContext);

const on_click_e0965ddb639bd8204affb7858dab4b9a = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.reflex_local_auth___local_auth____local_auth_state.uni_app___uni_app____app_state.open_pricing_modal", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])

  return (
    jsx(RadixThemesButton,{css:({ ["background"] : "linear-gradient(135deg, #0d0d0d 0%, #252525 50%, #1a1a1a 100%)", ["border"] : "none", ["cursor"] : "pointer", ["boxShadow"] : "0 4px 24px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.06)", ["transition"] : "all 0.25s ease", ["padding"] : "0 24px", ["&:hover"] : ({ ["boxShadow"] : "0 6px 32px rgba(255,255,255,0.1)", ["transform"] : "translateY(-2px)", ["filter"] : "brightness(1.2)" }), ["&:active"] : ({ ["transform"] : "translateY(0)" }), ["width"] : "100%", ["height"] : "68px", ["borderRadius"] : "16px" }),onClick:on_click_e0965ddb639bd8204affb7858dab4b9a},jsx(RadixThemesFlex,{align:"center",className:"rx-Stack",css:({ ["width"] : "100%" }),direction:"row",gap:"3"},jsx(RadixThemesText,{as:"p",css:({ ["textShadow"] : "0 1px 4px rgba(0,0,0,0.6)", ["fontWeight"] : "800", ["fontSize"] : "1rem", ["color"] : "white" })},"Unlock Unlimited Access"),jsx(RadixThemesFlex,{css:({ ["flex"] : 1, ["justifySelf"] : "stretch", ["alignSelf"] : "stretch" })},),jsx(RadixThemesText,{as:"p",css:({ ["color"] : "white", ["fontSize"] : "1.4rem", ["fontWeight"] : "bold" })},"\u2192")))
  )
}


function Fragment_5811f8067ea0c023b6a9c9fd3b406dc0 () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(Fragment,{},(reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.can_send_message_rx_state_?(jsx(Fragment,{},jsx(RadixThemesBox,{css:({ ["width"] : "100%" })},jsx(RadixThemesFlex,{align:"end",className:"rx-Stack",css:({ ["width"] : "100%" }),direction:"row",gap:"2"},jsx(Debounceinput_7f575e319ae587e4b20f9807e50f58c0,{},),jsx(Button_3dd99ab7326b698165a0e71d0e0a9aac,{},),jsx(Helmet,{},jsx("script",{},"\n(function(){\n  function attach(){\n    var ta = document.getElementById(\"chat_input\");\n    if(!ta) return false;\n    if(ta.dataset.enterSendAttached) return true;\n\n    ta.dataset.enterSendAttached = \"1\";\n\n    ta.addEventListener(\"keydown\", function(e){\n      if(e.key === \"Enter\" && !e.shiftKey){\n        e.preventDefault();\n        var btn = document.getElementById(\"chat_send_btn\");\n        if(btn && !btn.disabled){\n          btn.click();\n        }\n        setTimeout(function(){ try{ ta.focus(); }catch(err){} }, 0);\n      }\n    });\n\n    return true;\n  }\n\n  attach();\n  var t = 0;\n  var iv = setInterval(function(){\n    if(attach() || ++t > 60) clearInterval(iv);\n  }, 300);\n\n  try{\n    new MutationObserver(attach).observe(document.body,{childList:true,subtree:true});\n  }catch(e){}\n})();\n")))))):(jsx(Fragment,{},jsx(RadixThemesBox,{css:({ ["width"] : "100%", ["maxWidth"] : "860px", ["marginInlineStart"] : "auto", ["marginInlineEnd"] : "auto", ["padding"] : "1em" })},jsx(Button_48d61029118e4d0217ca909d5e2645b2,{},),jsx(RadixThemesText,{as:"p",css:({ ["color"] : "rgba(255,255,255,0.35)", ["fontSize"] : "0.7rem", ["textAlign"] : "center", ["marginTop"] : "8px" })},"\ud83d\udd12 You've reached your 5 free messages for today. Resets at midnight."))))))
  )
}


function Badge_5154d7cb792bdaa6953030f9a0973e60 () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(RadixThemesBadge,{css:({ ["background"] : (reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.is_premium_2_rx_state_ ? "linear-gradient(90deg,#7c3aed,#a855f7)" : (reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.is_premium_1_rx_state_ ? "linear-gradient(90deg,#b45309,#f59e0b)" : (reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.is_in_trial_rx_state_ ? "linear-gradient(90deg,#065f46,#10b981)" : "rgba(255,255,255,0.08)"))), ["color"] : "white", ["fontSize"] : "0.7rem", ["padding"] : "2px 10px", ["borderRadius"] : "20px" }),variant:"solid"},reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.tier_label_rx_state_)
  )
}


function Text_da2e487fd33e15dec904d4a288e84ad6 () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(RadixThemesText,{as:"p",css:({ ["color"] : "rgba(255,255,255,0.4)", ["fontSize"] : "0.72rem" })},((JSON.stringify(reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.messages_left_today_rx_state_))+" / 5 messages left today"))
  )
}


function Fragment_94ff4146aa81427eda8afdd5d5cf0f59 () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(Fragment,{},(((!(reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.is_premium_1_rx_state_) && !(reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.is_premium_2_rx_state_)) && !(reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.is_in_trial_rx_state_))?(jsx(Fragment,{},jsx(Text_da2e487fd33e15dec904d4a288e84ad6,{},))):(jsx(Fragment,{},))))
  )
}


function Text_5a8f800a0b12e4c70fe70a7f1dc71473 () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(RadixThemesText,{as:"p",css:({ ["color"] : "rgba(255,255,255,0.3)", ["fontSize"] : "0.68rem", ["fontFamily"] : "monospace", ["--default-font-family"] : "monospace" })},("\u26a1 "+reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.active_model_name_rx_state_))
  )
}


function Button_1a1be1efe95f3ca21a863798b10a4a7b () {
  const [addEvents, connectErrors] = useContext(EventLoopContext);

const on_click_f7c8735f915367a09ba984261a5a83a5 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.reflex_local_auth___local_auth____local_auth_state.uni_app___uni_app____app_state.close_pricing_modal", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])

  return (
    jsx(RadixThemesButton,{css:({ ["&:hover"] : ({ ["background"] : "rgba(255,255,255,0.15)", ["color"] : "white" }), ["position"] : "absolute", ["top"] : "16px", ["right"] : "20px", ["background"] : "rgba(255,255,255,0.08)", ["border"] : "none", ["color"] : "rgba(255,255,255,0.6)", ["fontSize"] : "1.1rem", ["borderRadius"] : "8px", ["width"] : "36px", ["height"] : "36px", ["cursor"] : "pointer" }),onClick:on_click_f7c8735f915367a09ba984261a5a83a5},"\u2715")
  )
}


function Fragment_6b24bc3a9d0dd1ef7cb37e41e65537f3 () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(Fragment,{},(reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.is_premium_1_rx_state_?(jsx(Fragment,{},jsx(RadixThemesBox,{css:({ ["position"] : "absolute", ["top"] : "-14px", ["left"] : "50%", ["transform"] : "translateX(-50%)", ["background"] : "linear-gradient(90deg,#065f46,#10b981)", ["padding"] : "4px 16px", ["borderRadius"] : "20px", ["whiteSpace"] : "nowrap" })},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "0.65rem", ["fontWeight"] : "800", ["letterSpacing"] : "2px", ["color"] : "white" })},"\u2713 YOUR PLAN")))):(jsx(Fragment,{},(false?(jsx(Fragment,{},jsx(RadixThemesBox,{css:({ ["position"] : "absolute", ["top"] : "-14px", ["left"] : "50%", ["transform"] : "translateX(-50%)", ["background"] : "linear-gradient(90deg,#7c3aed,#a855f7)", ["padding"] : "4px 16px", ["borderRadius"] : "20px", ["whiteSpace"] : "nowrap" })},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "0.65rem", ["fontWeight"] : "800", ["letterSpacing"] : "2px", ["color"] : "white" })},"\u2728 MOST POPULAR")))):(jsx(Fragment,{},)))))))
  )
}


function Fragment_1e1652087620580568ba82da8f647198 () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(Fragment,{},(reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.payment_processing_rx_state_?(jsx(Fragment,{},jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",direction:"row",gap:"2"},jsx(RadixThemesSpinner,{css:({ ["color"] : "white" }),size:"1"},),jsx(RadixThemesText,{as:"p"},"Redirecting...")))):(jsx(Fragment,{},jsx(RadixThemesText,{as:"p"},"Get Premium Fast  \u2192")))))
  )
}


function Button_e5d9373ed85388376855d35e03d1406f () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)
const [addEvents, connectErrors] = useContext(EventLoopContext);

const on_click_d2a80421709e7a20c3f9af278772ca84 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.reflex_local_auth___local_auth____local_auth_state.uni_app___uni_app____app_state.initiate_payment", ({ ["plan"] : 1 }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])

  return (
    jsx(RadixThemesButton,{css:({ ["background"] : "linear-gradient(135deg,#b45309,#f59e0b)", ["border"] : "none", ["color"] : "white", ["fontWeight"] : "700", ["fontSize"] : "0.9rem", ["cursor"] : "pointer", ["transition"] : "all 0.2s ease", ["&:hover"] : ({ ["filter"] : "brightness(1.12)", ["transform"] : "translateY(-1px)", ["boxShadow"] : "0 0 24px rgba(245,158,11,0.45)" }), ["&:active"] : ({ ["transform"] : "translateY(0)" }), ["width"] : "100%", ["height"] : "48px", ["borderRadius"] : "12px", ["isDisabled"] : reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.payment_processing_rx_state_ }),onClick:on_click_d2a80421709e7a20c3f9af278772ca84},jsx(Fragment_1e1652087620580568ba82da8f647198,{},))
  )
}


function Fragment_f9c943029b4fc3679a5488ad285d0569 () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(Fragment,{},(reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.is_premium_1_rx_state_?(jsx(Fragment,{},jsx(RadixThemesBox,{css:({ ["background"] : "rgba(16,185,129,0.12)", ["border"] : "1px solid rgba(16,185,129,0.35)", ["width"] : "100%", ["height"] : "48px", ["borderRadius"] : "12px", ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center" })},jsx(RadixThemesText,{as:"p",css:({ ["color"] : "rgba(255,255,255,0.5)", ["fontWeight"] : "700", ["fontSize"] : "0.9rem", ["textAlign"] : "center", ["width"] : "100%" })},"\u2713 Active Plan")))):(jsx(Fragment,{},jsx(Button_e5d9373ed85388376855d35e03d1406f,{},)))))
  )
}


function Box_946998ad470f7493e6e4680458034120 () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(RadixThemesBox,{css:({ ["boxShadow"] : (reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.is_premium_1_rx_state_ ? "0 0 24px rgba(16,185,129,0.25)" : (false ? "0 0 24px rgba(245,158,11,0.45)" : "0 4px 24px rgba(0,0,0,0.4)")), ["transition"] : "transform 0.2s ease", ["&:hover"] : ({ ["transform"] : "translateY(-4px)" }), ["position"] : "relative", ["background"] : "rgba(18,18,24,0.92)", ["border"] : (reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.is_premium_1_rx_state_ ? "1.5px solid rgba(16,185,129,0.5)" : (false ? "1.5px solid rgba(168,85,247,0.6)" : "1px solid rgba(255,255,255,0.1)")), ["borderRadius"] : "20px", ["width"] : "280px", ["flexShrink"] : "0", ["marginTop"] : ((false || reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.is_premium_1_rx_state_) ? "14px" : "0") })},jsx(Fragment_6b24bc3a9d0dd1ef7cb37e41e65537f3,{},),jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["alignItems"] : "flex-start", ["width"] : "100%", ["padding"] : "1.5em" }),direction:"column",gap:"4"},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "2.2rem" })},"\u26a1"),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "1.1rem", ["fontWeight"] : "700", ["color"] : "white", ["letterSpacing"] : "0.5px" })},"Premium Fast"),jsx(RadixThemesFlex,{align:"end",className:"rx-Stack",direction:"row",gap:"1"},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "2.5rem", ["fontWeight"] : "900", ["color"] : "white" })},"200"),jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["alignItems"] : "flex-start", ["paddingTop"] : "8px" }),direction:"column",gap:"0"},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "0.75rem", ["color"] : "rgba(255,255,255,0.6)", ["fontWeight"] : "600" })},"LKR"),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "0.7rem", ["color"] : "rgba(255,255,255,0.45)" })},"/month"))),jsx(RadixThemesBox,{css:({ ["background"] : "rgba(255,255,255,0.06)", ["borderRadius"] : "8px", ["padding"] : "6px 12px", ["width"] : "100%", ["textAlign"] : "center" })},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "0.72rem", ["color"] : "rgba(255,255,255,0.6)", ["fontFamily"] : "monospace", ["--default-font-family"] : "monospace" })},"\ud83e\udd16 llama-3.3-70b-fast")),jsx(RadixThemesSeparator,{css:({ ["borderColor"] : "rgba(255,255,255,0.1)", ["width"] : "100%" }),size:"4"},),jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["alignItems"] : "flex-start", ["width"] : "100%" }),direction:"column",gap:"2"},jsx(RadixThemesFlex,{align:"center",className:"rx-Stack",direction:"row",gap:"2"},jsx(RadixThemesText,{as:"p",css:({ ["color"] : "#00ff88", ["fontWeight"] : "700", ["fontSize"] : "0.85rem" })},"\u2713"),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "0.82rem", ["color"] : "rgba(255,255,255,0.8)" })},"Unlimited daily messages")),jsx(RadixThemesFlex,{align:"center",className:"rx-Stack",direction:"row",gap:"2"},jsx(RadixThemesText,{as:"p",css:({ ["color"] : "#00ff88", ["fontWeight"] : "700", ["fontSize"] : "0.85rem" })},"\u2713"),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "0.82rem", ["color"] : "rgba(255,255,255,0.8)" })},"Fast model")),jsx(RadixThemesFlex,{align:"center",className:"rx-Stack",direction:"row",gap:"2"},jsx(RadixThemesText,{as:"p",css:({ ["color"] : "#00ff88", ["fontWeight"] : "700", ["fontSize"] : "0.85rem" })},"\u2713"),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "0.82rem", ["color"] : "rgba(255,255,255,0.8)" })},"All semester modes")),jsx(RadixThemesFlex,{align:"center",className:"rx-Stack",direction:"row",gap:"2"},jsx(RadixThemesText,{as:"p",css:({ ["color"] : "#00ff88", ["fontWeight"] : "700", ["fontSize"] : "0.85rem" })},"\u2713"),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "0.82rem", ["color"] : "rgba(255,255,255,0.8)" })},"Priority response")),jsx(RadixThemesFlex,{align:"center",className:"rx-Stack",direction:"row",gap:"2"},jsx(RadixThemesText,{as:"p",css:({ ["color"] : "#00ff88", ["fontWeight"] : "700", ["fontSize"] : "0.85rem" })},"\u2713"),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "0.82rem", ["color"] : "rgba(255,255,255,0.8)" })},"Chat history saved"))),jsx(Fragment_f9c943029b4fc3679a5488ad285d0569,{},)))
  )
}


function Fragment_b1aac5e1b4b9e0900004cab24b02ec9f () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(Fragment,{},(reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.is_premium_2_rx_state_?(jsx(Fragment,{},jsx(RadixThemesBox,{css:({ ["position"] : "absolute", ["top"] : "-14px", ["left"] : "50%", ["transform"] : "translateX(-50%)", ["background"] : "linear-gradient(90deg,#065f46,#10b981)", ["padding"] : "4px 16px", ["borderRadius"] : "20px", ["whiteSpace"] : "nowrap" })},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "0.65rem", ["fontWeight"] : "800", ["letterSpacing"] : "2px", ["color"] : "white" })},"\u2713 YOUR PLAN")))):(jsx(Fragment,{},(true?(jsx(Fragment,{},jsx(RadixThemesBox,{css:({ ["position"] : "absolute", ["top"] : "-14px", ["left"] : "50%", ["transform"] : "translateX(-50%)", ["background"] : "linear-gradient(90deg,#7c3aed,#a855f7)", ["padding"] : "4px 16px", ["borderRadius"] : "20px", ["whiteSpace"] : "nowrap" })},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "0.65rem", ["fontWeight"] : "800", ["letterSpacing"] : "2px", ["color"] : "white" })},"\u2728 MOST POPULAR")))):(jsx(Fragment,{},)))))))
  )
}


function Fragment_36e6f6153c8082ff25d0b81be32e2f9a () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(Fragment,{},(reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.payment_processing_rx_state_?(jsx(Fragment,{},jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",direction:"row",gap:"2"},jsx(RadixThemesSpinner,{css:({ ["color"] : "white" }),size:"1"},),jsx(RadixThemesText,{as:"p"},"Redirecting...")))):(jsx(Fragment,{},jsx(RadixThemesText,{as:"p"},"Get Premium Pro  \u2192")))))
  )
}


function Button_f5b9dbd77a81a3aa7ab50e7296d9d6b0 () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)
const [addEvents, connectErrors] = useContext(EventLoopContext);

const on_click_8e6c3be0a02ebe0287f4bd46f58d6f25 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.reflex_local_auth___local_auth____local_auth_state.uni_app___uni_app____app_state.initiate_payment", ({ ["plan"] : 2 }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])

  return (
    jsx(RadixThemesButton,{css:({ ["background"] : "linear-gradient(135deg,#7c3aed,#a855f7)", ["border"] : "none", ["color"] : "white", ["fontWeight"] : "700", ["fontSize"] : "0.9rem", ["cursor"] : "pointer", ["transition"] : "all 0.2s ease", ["&:hover"] : ({ ["filter"] : "brightness(1.12)", ["transform"] : "translateY(-1px)", ["boxShadow"] : "0 0 28px rgba(168,85,247,0.5)" }), ["&:active"] : ({ ["transform"] : "translateY(0)" }), ["width"] : "100%", ["height"] : "48px", ["borderRadius"] : "12px", ["isDisabled"] : reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.payment_processing_rx_state_ }),onClick:on_click_8e6c3be0a02ebe0287f4bd46f58d6f25},jsx(Fragment_36e6f6153c8082ff25d0b81be32e2f9a,{},))
  )
}


function Fragment_f171d9658254aba5e6925b217cf9335c () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(Fragment,{},(reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.is_premium_2_rx_state_?(jsx(Fragment,{},jsx(RadixThemesBox,{css:({ ["background"] : "rgba(16,185,129,0.12)", ["border"] : "1px solid rgba(16,185,129,0.35)", ["width"] : "100%", ["height"] : "48px", ["borderRadius"] : "12px", ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center" })},jsx(RadixThemesText,{as:"p",css:({ ["color"] : "rgba(255,255,255,0.5)", ["fontWeight"] : "700", ["fontSize"] : "0.9rem", ["textAlign"] : "center", ["width"] : "100%" })},"\u2713 Active Plan")))):(jsx(Fragment,{},jsx(Button_f5b9dbd77a81a3aa7ab50e7296d9d6b0,{},)))))
  )
}


function Box_8b93ddbc10d42813834e821a8df6f61a () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(RadixThemesBox,{css:({ ["boxShadow"] : (reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.is_premium_2_rx_state_ ? "0 0 24px rgba(16,185,129,0.25)" : (true ? "0 0 28px rgba(168,85,247,0.5)" : "0 4px 24px rgba(0,0,0,0.4)")), ["transition"] : "transform 0.2s ease", ["&:hover"] : ({ ["transform"] : "translateY(-4px)" }), ["position"] : "relative", ["background"] : "rgba(18,18,24,0.92)", ["border"] : (reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.is_premium_2_rx_state_ ? "1.5px solid rgba(16,185,129,0.5)" : (true ? "1.5px solid rgba(168,85,247,0.6)" : "1px solid rgba(255,255,255,0.1)")), ["borderRadius"] : "20px", ["width"] : "280px", ["flexShrink"] : "0", ["marginTop"] : ((true || reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.is_premium_2_rx_state_) ? "14px" : "0") })},jsx(Fragment_b1aac5e1b4b9e0900004cab24b02ec9f,{},),jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["alignItems"] : "flex-start", ["width"] : "100%", ["padding"] : "1.5em" }),direction:"column",gap:"4"},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "2.2rem" })},"\ud83d\udc51"),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "1.1rem", ["fontWeight"] : "700", ["color"] : "white", ["letterSpacing"] : "0.5px" })},"Premium Pro"),jsx(RadixThemesFlex,{align:"end",className:"rx-Stack",direction:"row",gap:"1"},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "2.5rem", ["fontWeight"] : "900", ["color"] : "white" })},"500"),jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["alignItems"] : "flex-start", ["paddingTop"] : "8px" }),direction:"column",gap:"0"},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "0.75rem", ["color"] : "rgba(255,255,255,0.6)", ["fontWeight"] : "600" })},"LKR"),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "0.7rem", ["color"] : "rgba(255,255,255,0.45)" })},"/month"))),jsx(RadixThemesBox,{css:({ ["background"] : "rgba(255,255,255,0.06)", ["borderRadius"] : "8px", ["padding"] : "6px 12px", ["width"] : "100%", ["textAlign"] : "center" })},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "0.72rem", ["color"] : "rgba(255,255,255,0.6)", ["fontFamily"] : "monospace", ["--default-font-family"] : "monospace" })},"\ud83e\udd16 llama-3.3-70b-pro")),jsx(RadixThemesSeparator,{css:({ ["borderColor"] : "rgba(255,255,255,0.1)", ["width"] : "100%" }),size:"4"},),jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["alignItems"] : "flex-start", ["width"] : "100%" }),direction:"column",gap:"2"},jsx(RadixThemesFlex,{align:"center",className:"rx-Stack",direction:"row",gap:"2"},jsx(RadixThemesText,{as:"p",css:({ ["color"] : "#00ff88", ["fontWeight"] : "700", ["fontSize"] : "0.85rem" })},"\u2713"),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "0.82rem", ["color"] : "rgba(255,255,255,0.8)" })},"Unlimited daily messages")),jsx(RadixThemesFlex,{align:"center",className:"rx-Stack",direction:"row",gap:"2"},jsx(RadixThemesText,{as:"p",css:({ ["color"] : "#00ff88", ["fontWeight"] : "700", ["fontSize"] : "0.85rem" })},"\u2713"),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "0.82rem", ["color"] : "rgba(255,255,255,0.8)" })},"Powerful Pro model")),jsx(RadixThemesFlex,{align:"center",className:"rx-Stack",direction:"row",gap:"2"},jsx(RadixThemesText,{as:"p",css:({ ["color"] : "#00ff88", ["fontWeight"] : "700", ["fontSize"] : "0.85rem" })},"\u2713"),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "0.82rem", ["color"] : "rgba(255,255,255,0.8)" })},"Deeper explanations")),jsx(RadixThemesFlex,{align:"center",className:"rx-Stack",direction:"row",gap:"2"},jsx(RadixThemesText,{as:"p",css:({ ["color"] : "#00ff88", ["fontWeight"] : "700", ["fontSize"] : "0.85rem" })},"\u2713"),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "0.82rem", ["color"] : "rgba(255,255,255,0.8)" })},"All semester modes")),jsx(RadixThemesFlex,{align:"center",className:"rx-Stack",direction:"row",gap:"2"},jsx(RadixThemesText,{as:"p",css:({ ["color"] : "#00ff88", ["fontWeight"] : "700", ["fontSize"] : "0.85rem" })},"\u2713"),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "0.82rem", ["color"] : "rgba(255,255,255,0.8)" })},"Priority response"))),jsx(Fragment_f171d9658254aba5e6925b217cf9335c,{},)))
  )
}


function Text_5a5efdd24b5212d18d324bd183b41d43 () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(RadixThemesText,{as:"p",css:({ ["color"] : "#fca5a5", ["fontSize"] : "0.82rem", ["textAlign"] : "center" })},("\u26a0\ufe0f  "+reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.payment_error_rx_state_))
  )
}


function Fragment_e4f467593da644c913b28efdf8c30999 () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(Fragment,{},(!((reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.payment_error_rx_state_?.valueOf?.() === ""?.valueOf?.()))?(jsx(Fragment,{},jsx(RadixThemesBox,{css:({ ["background"] : "rgba(239,68,68,0.1)", ["border"] : "1px solid rgba(239,68,68,0.3)", ["borderRadius"] : "10px", ["padding"] : "10px 20px", ["marginTop"] : "1.5em", ["width"] : "100%", ["maxWidth"] : "580px" })},jsx(Text_5a5efdd24b5212d18d324bd183b41d43,{},)))):(jsx(Fragment,{},))))
  )
}


function Fragment_d1e0d8416ebf86e4fc50aac73c3661ec () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(Fragment,{},(reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.show_pricing_modal_rx_state_?(jsx(Fragment,{},jsx(RadixThemesBox,{css:({ ["backdropFilter"] : "blur(6px)", ["position"] : "fixed", ["top"] : "0", ["left"] : "0", ["width"] : "100vw", ["height"] : "100vh", ["zIndex"] : "1000", ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center", ["background"] : "rgba(0,0,0,0.75)", ["padding"] : "1em" })},jsx(RadixThemesBox,{css:({ ["boxShadow"] : "0 32px 80px rgba(0,0,0,0.8), 0 0 0 1px rgba(255,255,255,0.04)", ["backdropFilter"] : "blur(20px)", ["position"] : "relative", ["background"] : "rgba(10,10,14,0.97)", ["border"] : "1px solid rgba(255,255,255,0.08)", ["borderRadius"] : "24px", ["padding"] : "2.5em 2em", ["display"] : "flex", ["flexDirection"] : "column", ["alignItems"] : "center", ["width"] : "100%", ["maxWidth"] : "680px" })},jsx(Button_1a1be1efe95f3ca21a863798b10a4a7b,{},),jsx(RadixThemesFlex,{align:"center",className:"rx-Stack",css:({ ["marginBottom"] : "2em" }),direction:"column",gap:"2"},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "1.7rem", ["fontWeight"] : "800", ["color"] : "white", ["letterSpacing"] : "-0.5px" })},"Upgrade Alex AI"),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "0.88rem", ["color"] : "rgba(255,255,255,0.45)", ["textAlign"] : "center", ["maxWidth"] : "380px" })},"Unlock unlimited learning \u2014 no daily caps, faster responses.")),jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["flexWrap"] : "wrap" }),direction:"row",justify:"center",gap:"5"},jsx(Box_946998ad470f7493e6e4680458034120,{},),jsx(Box_8b93ddbc10d42813834e821a8df6f61a,{},)),jsx(Fragment_e4f467593da644c913b28efdf8c30999,{},),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "0.72rem", ["color"] : "rgba(255,255,255,0.25)", ["textAlign"] : "center", ["marginTop"] : "2em" })},"\ud83d\udd12 Secure checkout via PayHere  \u00b7  Cancel anytime  \u00b7  Instant activation"))))):(jsx(Fragment,{},))))
  )
}


        function ComponentMap_d59534cfa3df3086665270d8af3d1699 () {
            const { resolvedColorMode } = useContext(ColorModeContext)



            return (
                ({ ["h1"] : (({node, children, ...props}) => (jsx(RadixThemesHeading,{as:"h1",css:({ ["marginTop"] : "0.5em", ["marginBottom"] : "0.5em" }),size:"6",...props},children))), ["h2"] : (({node, children, ...props}) => (jsx(RadixThemesHeading,{as:"h2",css:({ ["marginTop"] : "0.5em", ["marginBottom"] : "0.5em" }),size:"5",...props},children))), ["h3"] : (({node, children, ...props}) => (jsx(RadixThemesHeading,{as:"h3",css:({ ["marginTop"] : "0.5em", ["marginBottom"] : "0.5em" }),size:"4",...props},children))), ["h4"] : (({node, children, ...props}) => (jsx(RadixThemesHeading,{as:"h4",css:({ ["marginTop"] : "0.5em", ["marginBottom"] : "0.5em" }),size:"3",...props},children))), ["h5"] : (({node, children, ...props}) => (jsx(RadixThemesHeading,{as:"h5",css:({ ["marginTop"] : "0.5em", ["marginBottom"] : "0.5em" }),size:"2",...props},children))), ["h6"] : (({node, children, ...props}) => (jsx(RadixThemesHeading,{as:"h6",css:({ ["marginTop"] : "0.5em", ["marginBottom"] : "0.5em" }),size:"1",...props},children))), ["p"] : (({node, children, ...props}) => (jsx(RadixThemesText,{as:"p",css:({ ["marginTop"] : "1em", ["marginBottom"] : "1em" }),...props},children))), ["ul"] : (({node, children, ...props}) => (jsx("ul",{css:({ ["listStyleType"] : "disc", ["marginTop"] : "1em", ["marginBottom"] : "1em", ["marginLeft"] : "1.5rem", ["direction"] : "column" }),...props},children))), ["ol"] : (({node, children, ...props}) => (jsx("ol",{css:({ ["listStyleType"] : "decimal", ["marginTop"] : "1em", ["marginBottom"] : "1em", ["marginLeft"] : "1.5rem", ["direction"] : "column" }),...props},children))), ["li"] : (({node, children, ...props}) => (jsx("li",{css:({ ["marginTop"] : "0.5em", ["marginBottom"] : "0.5em" }),...props},children))), ["a"] : (({node, children, ...props}) => (jsx(RadixThemesLink,{css:({ ["&:hover"] : ({ ["color"] : "var(--accent-8)" }) }),href:"#",...props},children))), ["code"] : (({node, children, ...props}) => (jsx(RadixThemesCode,{...props},children))), ["pre"] : (({node, ...rest}) => { const {node: childNode, className, children: components, ...props} = rest.children.props; const children = String(Array.isArray(components) ? components.join('\n') : components).replace(/\n$/, ''); const match = (className || '').match(/language-(?<lang>.*)/); let _language = match ? match[1] : ''; ;             return jsx(SyntaxHighlighter,{children:children,css:({ ["marginTop"] : "1em", ["marginBottom"] : "1em" }),language:_language,style:((resolvedColorMode?.valueOf?.() === "light"?.valueOf?.()) ? oneLight : oneDark),wrapLongLines:true,...props},);         }) })
            )
        }
        

function Fragment_ad78a0cf9e338d13bf310c5a2f058e32 () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(Fragment,{},(reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.is_processing_rx_state_?(jsx(Fragment,{},jsx("div",{className:"rx-Html",dangerouslySetInnerHTML:({ ["__html"] : "\n                        <div style=\"width:24px;height:24px;position:relative;margin-bottom:10px;\">\n                          <style>\n                            @keyframes alexorbit {\n                              from { transform: rotate(0deg) translateX(10px); }\n                              to   { transform: rotate(360deg) translateX(10px); }\n                            }\n                          </style>\n                          <div style=\"\n                            width:4px;height:4px;\n                            background:#FFD700;\n                            border-radius:50%;\n                            position:absolute;\n                            top:50%;left:50%;\n                            margin-top:-2px;margin-left:-2px;\n                            animation:alexorbit 0.3s linear infinite;\n                            box-shadow:0 0 4px rgba(255,215,0,0.9);\n                          \"></div>\n                        </div>\n                    " })},))):(jsx(Fragment,{},))))
  )
}


function Flex_fa24af3a22479ec0201cd0e32d48aedf () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)
const ref_chat_bottom_anchor = useRef(null); refs["ref_chat_bottom_anchor"] = ref_chat_bottom_anchor;



  return (
    jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["width"] : "100%", ["maxWidth"] : "760px", ["marginInlineStart"] : "auto", ["marginInlineEnd"] : "auto", ["paddingInlineStart"] : "2em", ["paddingInlineEnd"] : "2em", ["paddingBottom"] : "1em" }),direction:"column",gap:"3"},Array.prototype.map.call(reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.chat_history_rx_state_ ?? [],((msg_rx_state_,index_cbd00b2c00b1cb217515c1a31d1dfbfc)=>(jsx(RadixThemesBox,{css:({ ["width"] : "100%", ["marginBottom"] : "16px", ["display"] : "flex", ["flexDirection"] : "column" }),key:index_cbd00b2c00b1cb217515c1a31d1dfbfc},jsx(Fragment,{},((msg_rx_state_?.["role"]?.valueOf?.() === "user"?.valueOf?.())?(jsx(Fragment,{},jsx(RadixThemesBox,{css:({ ["background"] : "rgba(255,255,255,0.08)", ["borderRadius"] : "18px 18px 4px 18px", ["padding"] : "10px 16px", ["maxWidth"] : "70%", ["marginLeft"] : "auto", ["marginRight"] : "0" })},jsx(RadixThemesText,{as:"p",css:({ ["color"] : "white", ["fontSize"] : "0.95rem" })},msg_rx_state_?.["content"])))):(jsx(Fragment,{},jsx(RadixThemesBox,{css:({ ["color"] : "rgba(255,255,255,0.95)", ["fontSize"] : "0.95rem", ["maxWidth"] : "85%", ["marginLeft"] : "0" })},jsx("div",{},jsx(ReactMarkdown,{components:ComponentMap_d59534cfa3df3086665270d8af3d1699(),rehypePlugins:[rehypeKatex, rehypeRaw, rehypeUnwrapImages],remarkPlugins:[remarkMath, remarkGfm]},msg_rx_state_?.["content"]))))))))))),jsx(Fragment_ad78a0cf9e338d13bf310c5a2f058e32,{},),jsx(RadixThemesBox,{css:({ ["height"] : "1px" }),id:"chat_bottom_anchor",ref:ref_chat_bottom_anchor},))
  )
}


function Fragment_5379204efa2689dab5acca04a2441b26 () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(Fragment,{},(reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.can_send_message_rx_state_?(jsx(Fragment,{},jsx(RadixThemesBox,{css:({ ["width"] : "100%", ["maxWidth"] : "860px", ["marginInlineStart"] : "auto", ["marginInlineEnd"] : "auto", ["padding"] : "0 1em 1em 1em" })},jsx(RadixThemesFlex,{align:"end",className:"rx-Stack",css:({ ["width"] : "100%" }),direction:"row",gap:"2"},jsx(Debounceinput_7f575e319ae587e4b20f9807e50f58c0,{},),jsx(Button_3dd99ab7326b698165a0e71d0e0a9aac,{},),jsx(Helmet,{},jsx("script",{},"\n(function(){\n  function attach(){\n    var ta = document.getElementById(\"chat_input\");\n    if(!ta) return false;\n    if(ta.dataset.enterSendAttached) return true;\n\n    ta.dataset.enterSendAttached = \"1\";\n\n    ta.addEventListener(\"keydown\", function(e){\n      if(e.key === \"Enter\" && !e.shiftKey){\n        e.preventDefault();\n        var btn = document.getElementById(\"chat_send_btn\");\n        if(btn && !btn.disabled){\n          btn.click();\n        }\n        setTimeout(function(){ try{ ta.focus(); }catch(err){} }, 0);\n      }\n    });\n\n    return true;\n  }\n\n  attach();\n  var t = 0;\n  var iv = setInterval(function(){\n    if(attach() || ++t > 60) clearInterval(iv);\n  }, 300);\n\n  try{\n    new MutationObserver(attach).observe(document.body,{childList:true,subtree:true});\n  }catch(e){}\n})();\n")))))):(jsx(Fragment,{},jsx(RadixThemesBox,{css:({ ["width"] : "100%", ["maxWidth"] : "860px", ["marginInlineStart"] : "auto", ["marginInlineEnd"] : "auto", ["padding"] : "1em" })},jsx(Button_48d61029118e4d0217ca909d5e2645b2,{},),jsx(RadixThemesText,{as:"p",css:({ ["color"] : "rgba(255,255,255,0.35)", ["fontSize"] : "0.7rem", ["textAlign"] : "center", ["marginTop"] : "8px" })},"\ud83d\udd12 You've reached your 5 free messages for today. Resets at midnight."))))))
  )
}


function Fragment_d6df190244a4a99e98fdd2c2f2ba598e () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)
const ref_chat_scroll = useRef(null); refs["ref_chat_scroll"] = ref_chat_scroll;



  return (
    jsx(Fragment,{},(reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.is_empty_chat_rx_state_?(jsx(Fragment,{},jsx(RadixThemesBox,{css:({ ["width"] : "100%", ["height"] : "100%", ["display"] : "flex", ["flexDirection"] : "column", ["alignItems"] : "center", ["justifyContent"] : "center", ["background"] : "transparent", ["padding"] : "2em" })},jsx(RadixThemesFlex,{align:"center",className:"rx-Stack",css:({ ["width"] : "100%", ["height"] : "100%" }),direction:"column",gap:"4"},jsx(RadixThemesFlex,{css:({ ["flex"] : 1, ["justifySelf"] : "stretch", ["alignSelf"] : "stretch" })},),jsx("img",{css:({ ["filter"] : "drop-shadow(0 0 20px rgba(255,215,0,0.4)) drop-shadow(0 0 40px rgba(0,255,136,0.15))", ["opacity"] : "0.92", ["width"] : "120px", ["height"] : "120px", ["objectFit"] : "contain" }),src:"/a_logo.png"},),jsx(RadixThemesText,{as:"p",css:({ ["color"] : "rgba(255,255,255,0.55)", ["fontSize"] : "1.05rem", ["fontWeight"] : "400", ["letterSpacing"] : "0.3px" })},"What do you want to learn today?"),jsx(RadixThemesFlex,{css:({ ["flex"] : 1, ["justifySelf"] : "stretch", ["alignSelf"] : "stretch" })},),jsx(RadixThemesBox,{css:({ ["width"] : "100%", ["maxWidth"] : "680px" })},jsx(Fragment_5811f8067ea0c023b6a9c9fd3b406dc0,{},)),jsx(RadixThemesFlex,{align:"center",className:"rx-Stack",css:({ ["width"] : "100%", ["maxWidth"] : "860px", ["marginInlineStart"] : "auto", ["marginInlineEnd"] : "auto", ["paddingInlineStart"] : "1em", ["paddingInlineEnd"] : "1em", ["paddingTop"] : "4px", ["paddingBottom"] : "4px" }),direction:"row",gap:"3"},jsx(Badge_5154d7cb792bdaa6953030f9a0973e60,{},),jsx(Fragment_94ff4146aa81427eda8afdd5d5cf0f59,{},),jsx(RadixThemesFlex,{css:({ ["flex"] : 1, ["justifySelf"] : "stretch", ["alignSelf"] : "stretch" })},),jsx(Text_5a8f800a0b12e4c70fe70a7f1dc71473,{},)),jsx(RadixThemesFlex,{css:({ ["flex"] : 1, ["justifySelf"] : "stretch", ["alignSelf"] : "stretch", ["height"] : "16em" })},)),jsx(Fragment_d1e0d8416ebf86e4fc50aac73c3661ec,{},)))):(jsx(Fragment,{},jsx(RadixThemesBox,{css:({ ["width"] : "100%", ["height"] : "100%", ["display"] : "flex", ["flexDirection"] : "column", ["overflow"] : "hidden", ["background"] : "transparent", ["position"] : "relative" })},jsx(RadixThemesBox,{css:({ ["flex"] : "1", ["minHeight"] : "0", ["overflowY"] : "auto", ["padding"] : "1em", ["width"] : "100%" }),id:"chat_scroll",ref:ref_chat_scroll},jsx(Flex_fa24af3a22479ec0201cd0e32d48aedf,{},)),jsx(Helmet,{},jsx("script",{},"\n(function(){\n  function attach(){\n    const box = document.getElementById(\"chat_scroll\");\n    if(!box) return false;\n    if(box.__autoScrollAttached) return true;\n    box.__autoScrollAttached = true;\n\n    const atBottom = () => (box.scrollHeight - box.scrollTop - box.clientHeight) < 80;\n    let userLocked = false;\n\n    const scrollNow = () => {\n      if(userLocked) return;\n      box.scrollTop = box.scrollHeight;\n    };\n\n    box.addEventListener(\"scroll\", () => {\n      userLocked = !atBottom();\n    });\n\n    const obs = new MutationObserver(() => {\n      requestAnimationFrame(scrollNow);\n      setTimeout(scrollNow, 0);\n      setTimeout(scrollNow, 80);\n      setTimeout(scrollNow, 250);\n      setTimeout(scrollNow, 600);\n    });\n\n    obs.observe(box, { childList: true, subtree: true });\n\n    scrollNow();\n    return true;\n  }\n\n  let tries = 0;\n  const iv = setInterval(() => {\n    tries += 1;\n    if(attach() || tries > 200) clearInterval(iv);\n  }, 50);\n})();\n")),jsx(RadixThemesFlex,{align:"center",className:"rx-Stack",css:({ ["width"] : "100%", ["maxWidth"] : "860px", ["marginInlineStart"] : "auto", ["marginInlineEnd"] : "auto", ["paddingInlineStart"] : "1em", ["paddingInlineEnd"] : "1em", ["paddingTop"] : "4px", ["paddingBottom"] : "4px" }),direction:"row",gap:"3"},jsx(Badge_5154d7cb792bdaa6953030f9a0973e60,{},),jsx(Fragment_94ff4146aa81427eda8afdd5d5cf0f59,{},),jsx(RadixThemesFlex,{css:({ ["flex"] : 1, ["justifySelf"] : "stretch", ["alignSelf"] : "stretch" })},),jsx(Text_5a8f800a0b12e4c70fe70a7f1dc71473,{},)),jsx(Fragment_5379204efa2689dab5acca04a2441b26,{},),jsx(Fragment_d1e0d8416ebf86e4fc50aac73c3661ec,{},))))))
  )
}


function Button_83b90ddc226b0d571b9580446c0e9db3 () {
  const [addEvents, connectErrors] = useContext(EventLoopContext);

const on_click_8661a2f475029198edf5511d82fd0c27 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.reflex_local_auth___local_auth____local_auth_state.uni_app___uni_app____app_state.go_home", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])

  return (
    jsx(RadixThemesButton,{color:"green",onClick:on_click_8661a2f475029198edf5511d82fd0c27,variant:"outline"},"Back to home")
  )
}


function Heading_78155d5466836033b29f7120027eae39 () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(RadixThemesHeading,{css:({ ["color"] : "white", ["fontFamily"] : "monospace", ["--default-font-family"] : "monospace", ["letterSpacing"] : "2px" }),size:"6"},reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.semester_short_label_rx_state_)
  )
}


function Text_ff700613efcf25674e1d426aa35471d9 () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(RadixThemesText,{as:"p"},reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.current_day_rx_state_)
  )
}


function Fragment_1a65e15def6c2d176ade879e23d4432a () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(Fragment,{},(reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.is_generating_plan_rx_state_?(jsx(Fragment,{},jsx(RadixThemesFlex,{css:({ ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center", ["paddingTop"] : "2em", ["flexShrink"] : "0" })},jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",direction:"column",gap:"4"},jsx(RadixThemesSpinner,{css:({ ["color"] : "green" }),size:"3"},),jsx(RadixThemesText,{as:"p",css:({ ["color"] : "#00ff88", ["fontSize"] : "1.2em" })},"\ud83e\udde0 Generating your 110-day study plan..."))))):(jsx(Fragment,{},))))
  )
}


function Fragment_742aa4e1da416c833cc0c80baaebdd21 () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(Fragment,{},((reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.view_mode_rx_state_?.valueOf?.() === "home"?.valueOf?.())?(jsx(Fragment,{},jsx(RadixThemesBox,{css:({ ["height"] : "100vh", ["overflow"] : "hidden", ["display"] : "flex", ["flexDirection"] : "column", ["background"] : "radial-gradient(circle at bottom right,#002d1a 0%,#050505 100%)" })},jsx(RadixThemesBox,{css:({ ["position"] : "relative", ["display"] : "flex", ["alignItems"] : "center", ["width"] : "100%", ["padding"] : "2em", ["flexShrink"] : "0" })},jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["alignItems"] : "flex-start", ["flexDirection"] : "column" }),direction:"row",gap:"3"},jsx(RadixThemesHeading,{},jsx(RadixThemesText,{as:"p",css:({ ["color"] : "white" })},"Hi "),jsx(Text_de6457553040f2445b96779a74733a8a,{},)),jsx(Text_3a59335c13efa3792704b92daa5ff0f5,{},)),jsx(RadixThemesBox,{css:({ ["position"] : "absolute", ["left"] : "50%", ["transform"] : "translateX(-50%)" })},jsx(RadixThemesText,{as:"p",css:({ ["color"] : "#FFD700", ["fontSize"] : "3.5rem", ["fontWeight"] : "bold", ["letterSpacing"] : "4px", ["textShadow"] : "0 0 20px rgba(255,215,0,0.4)" })},"Alex AI")),jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["marginLeft"] : "auto" }),direction:"row",gap:"2"},jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["color"] : "#00ff88", ["fontWeight"] : "bold" }),direction:"row",gap:"3"},jsx(RadixThemesText,{as:"p"},"Streak: "),jsx(Text_8c52ca47f1fbef0fa724c97bdf85532e,{},),jsx(RadixThemesText,{as:"p"},"D")),jsx(Button_439d97f8c460f4e9420e6abf6128efec,{},),jsx(Button_7e24b63790dbafb0c037bec8fa2966f7,{},))),jsx(RadixThemesFlex,{css:({ ["width"] : "100%", ["flex"] : "1", ["minHeight"] : "0", ["alignItems"] : "stretch", ["overflow"] : "hidden" })},jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["width"] : "30%", ["padding"] : "2em", ["alignItems"] : "flex-start", ["height"] : "100%", ["minHeight"] : "0", ["overflow"] : "hidden" }),direction:"column",gap:"4"},jsx(RadixThemesText,{as:"p",css:({ ["color"] : "gray", ["fontSize"] : "0.8em", ["letterSpacing"] : "2px" })},"ACADEMIC YEAR"),jsx(Fragment_76171a76cc42899e898bf7ebf601bc5c,{},),jsx(Fragment_e7c2f63737b72a5f03ff48c76165e43f,{},),jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",direction:"column",gap:"3"},jsx("img",{css:({ ["width"] : "80px", ["height"] : "80px", ["objectFit"] : "contain", ["borderRadius"] : "12px", ["opacity"] : "0.85", ["marginInlineStart"] : "auto", ["marginInlineEnd"] : "auto" }),src:"/a_logo.png"},),jsx(Fragment_6e5f194f68861ca536a3dffa5fd809b4,{},)),jsx(RadixThemesBox,{css:({ ["width"] : "100%", ["paddingTop"] : "1em" })},jsx(RadixThemesText,{as:"p",css:({ ["color"] : "gray", ["fontSize"] : "0.8em", ["letterSpacing"] : "2px" })},"CHATS"),jsx(Flex_8a4bb67a523bd4bf4fc86db456f6d671,{},))),jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["width"] : "65%", ["height"] : "100%", ["minHeight"] : "0", ["overflow"] : "hidden" }),direction:"column",gap:"3"},jsx(Fragment_d6df190244a4a99e98fdd2c2f2ba598e,{},)))))):(jsx(Fragment,{},jsx(RadixThemesBox,{css:({ ["width"] : "100%", ["height"] : "100vh", ["maxHeight"] : "100vh", ["display"] : "flex", ["flexDirection"] : "column", ["overflow"] : "hidden", ["background"] : "radial-gradient(circle at bottom right,#002d1a 0%,#050505 100%)" })},jsx(RadixThemesFlex,{align:"center",className:"rx-Stack",css:({ ["width"] : "100%", ["padding"] : "1em 2em", ["flexShrink"] : "0" }),direction:"row",gap:"3"},jsx(Button_83b90ddc226b0d571b9580446c0e9db3,{},),jsx(Heading_78155d5466836033b29f7120027eae39,{},),jsx(RadixThemesFlex,{css:({ ["flex"] : 1, ["justifySelf"] : "stretch", ["alignSelf"] : "stretch" })},),jsx(RadixThemesBadge,{color:"blue",size:"2",variant:"solid"},jsx(RadixThemesText,{as:"p"},"Day "),jsx(Text_ff700613efcf25674e1d426aa35471d9,{},),jsx(RadixThemesText,{as:"p"},"/110"))),jsx(Fragment_1a65e15def6c2d176ade879e23d4432a,{},),jsx(RadixThemesBox,{css:({ ["width"] : "100%", ["flex"] : "1", ["minHeight"] : "0", ["overflow"] : "hidden" })},jsx(Fragment_d6df190244a4a99e98fdd2c2f2ba598e,{},)),jsx("div",{className:"rx-Html",dangerouslySetInnerHTML:({ ["__html"] : "<style>@keyframes bounce{0%,100%{transform:translateY(0);opacity:0.4;}50%{transform:translateY(-6px);opacity:1;}}</style>" })},))))))
  )
}


function Button_1b63f8611cbac980151c7de3071e0e01 () {
  const [addEvents, connectErrors] = useContext(EventLoopContext);

const on_click_73fe77bec015b6cc2d4248b8367972a9 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.reflex_local_auth___local_auth____local_auth_state.uni_app___uni_app____app_state.next_step", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])

  return (
    jsx(RadixThemesButton,{color:"green",css:({ ["animation"] : "pulse_glow 2s infinite", ["cursor"] : "pointer" }),onClick:on_click_73fe77bec015b6cc2d4248b8367972a9,size:"3"},"YES")
  )
}


function Fragment_2ae4c1713868712afcf068884412378b () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(Fragment,{},((reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.step_rx_state_?.valueOf?.() === 0?.valueOf?.())?(jsx(Fragment,{},jsx(RadixThemesBox,{css:({ ["backgroundImage"] : "url('/bg_image.png')", ["backgroundSize"] : "cover", ["width"] : "100vw", ["height"] : "100vh", ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center" })},jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",direction:"column",gap:"3"},jsx(RadixThemesHeading,{size:"8"},"Shall we begin"),jsx(Button_1b63f8611cbac980151c7de3071e0e01,{},))))):(jsx(Fragment,{},))))
  )
}


function Select__group_0cf93da5f6b5554989efbc4eddc12b68 () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(RadixThemesSelect.Group,{},"",Array.prototype.map.call(reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.options_rx_state_ ?? [],((item_rx_state_,index_9823cf83aa70cfbb1602bac35e8f2f1e)=>(jsx(RadixThemesSelect.Item,{key:index_9823cf83aa70cfbb1602bac35e8f2f1e,value:item_rx_state_},item_rx_state_)))))
  )
}


function Select__root_afc7ee75b7ab478228d6604b4c495bcd () {
  const [addEvents, connectErrors] = useContext(EventLoopContext);

const on_change_b9d86b371eea9386b38e41d70a960c68 = useCallback(((_ev_0) => (addEvents([(ReflexEvent("reflex___state____state.reflex_local_auth___local_auth____local_auth_state.uni_app___uni_app____app_state.set_degree", ({ ["value"] : _ev_0 }), ({  })))], [_ev_0], ({  })))), [addEvents, ReflexEvent])

  return (
    jsx(RadixThemesSelect.Root,{onValueChange:on_change_b9d86b371eea9386b38e41d70a960c68},jsx(RadixThemesSelect.Trigger,{css:({ ["width"] : "100%" }),placeholder:"Choose your degree"},),jsx(RadixThemesSelect.Content,{},jsx(Select__group_0cf93da5f6b5554989efbc4eddc12b68,{},)))
  )
}


function Button_d8a7c74d806330c787c4d93a94ac9822 () {
  const [addEvents, connectErrors] = useContext(EventLoopContext);

const on_click_73fe77bec015b6cc2d4248b8367972a9 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.reflex_local_auth___local_auth____local_auth_state.uni_app___uni_app____app_state.next_step", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])

  return (
    jsx(RadixThemesButton,{color:"green",onClick:on_click_73fe77bec015b6cc2d4248b8367972a9,size:"3"},"next")
  )
}


function Fragment_45acaac658ec8192ea337e6f92a2fc03 () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(Fragment,{},((reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.step_rx_state_?.valueOf?.() === 1?.valueOf?.())?(jsx(Fragment,{},jsx(RadixThemesBox,{css:({ ["backgroundImage"] : "url('/bg_image.png')", ["backgroundSize"] : "cover", ["width"] : "100vw", ["height"] : "100vh", ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center" })},jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",direction:"column",gap:"3"},jsx(RadixThemesHeading,{size:"7"},"Whats your degree"),jsx(Select__root_afc7ee75b7ab478228d6604b4c495bcd,{},),jsx(Button_d8a7c74d806330c787c4d93a94ac9822,{},))))):(jsx(Fragment,{},))))
  )
}


function Textfield__root_89973df696b0a85482d685275c796b02 () {
  const [addEvents, connectErrors] = useContext(EventLoopContext);

const on_change_130b943552d619be67301d13c8e5b372 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.reflex_local_auth___local_auth____local_auth_state.uni_app___uni_app____app_state.set_name", ({ ["value"] : _e?.["target"]?.["value"] }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])

  return (
    jsx(RadixThemesTextField.Root,{css:({ ["width"] : "100%" }),onChange:on_change_130b943552d619be67301d13c8e5b372,placeholder:"Enter your name",size:"3"},)
  )
}


function Button_0812414372e3044fa6227f243d24c587 () {
  const [addEvents, connectErrors] = useContext(EventLoopContext);

const on_click_73fe77bec015b6cc2d4248b8367972a9 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.reflex_local_auth___local_auth____local_auth_state.uni_app___uni_app____app_state.next_step", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])

  return (
    jsx(RadixThemesButton,{color:"green",onClick:on_click_73fe77bec015b6cc2d4248b8367972a9,size:"3"},"Next")
  )
}


function Fragment_c7217939049d6e446a1da844a3ca962f () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(Fragment,{},((reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.step_rx_state_?.valueOf?.() === 2?.valueOf?.())?(jsx(Fragment,{},jsx(RadixThemesBox,{css:({ ["backgroundImage"] : "url('/bg_image.png')", ["backgroundSize"] : "cover", ["width"] : "100vw", ["height"] : "100vh", ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center" })},jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["width"] : "400px" }),direction:"column",gap:"4"},jsx(RadixThemesHeading,{css:({ ["color"] : "white" }),size:"7"},"What's your name?"),jsx(Textfield__root_89973df696b0a85482d685275c796b02,{},),jsx(Button_0812414372e3044fa6227f243d24c587,{},))))):(jsx(Fragment,{},))))
  )
}


function Text_9fa24e182446fcb32ef02d505ecc5163 () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(RadixThemesText,{as:"p"},reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.degree_rx_state_)
  )
}


function Button_113c490837b491ffb6690b6014e4055b () {
  const [addEvents, connectErrors] = useContext(EventLoopContext);

const on_click_34d1bd69a14a271958942e9496578ef5 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.reflex_local_auth___local_auth____local_auth_state.uni_app___uni_app____app_state.start_app", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])

  return (
    jsx(RadixThemesButton,{color:"green",css:({ ["animation"] : "pulse_glow 2s infinite" }),onClick:on_click_34d1bd69a14a271958942e9496578ef5,size:"3"},"begin")
  )
}


function Fragment_5739af76947d76dba90e127f1e8eb825 () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(Fragment,{},((reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.step_rx_state_?.valueOf?.() === 3?.valueOf?.())?(jsx(Fragment,{},jsx(RadixThemesBox,{css:({ ["backgroundImage"] : "url('/bg_image.png')", ["backgroundSize"] : "cover", ["width"] : "100vw", ["height"] : "100vh", ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center" })},jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",direction:"column",gap:"3"},jsx(RadixThemesHeading,{size:"7"},jsx(RadixThemesText,{as:"p"},"Lets crush "),jsx(Text_9fa24e182446fcb32ef02d505ecc5163,{},)),jsx(RadixThemesText,{as:"p"},"You have 5 main subjects to master"),jsx(Button_113c490837b491ffb6690b6014e4055b,{},))))):(jsx(Fragment,{},))))
  )
}


function Fragment_52fae045429d36bc79e4818fbaaf1576 () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state)



  return (
    jsx(Fragment,{},(reflex___state____state__reflex_local_auth___local_auth____local_auth_state__uni_app___uni_app____app_state.is_started_rx_state_?(jsx(Fragment_742aa4e1da416c833cc0c80baaebdd21,{},)):(jsx(Fragment,{},jsx(RadixThemesBox,{css:({ ["height"] : "100vh" })},jsx(RadixThemesFlex,{css:({ ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center" })},jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",direction:"column",gap:"4"},jsx(Fragment_2ae4c1713868712afcf068884412378b,{},),jsx(Fragment_45acaac658ec8192ea337e6f92a2fc03,{},),jsx(Fragment_c7217939049d6e446a1da844a3ca962f,{},),jsx(Fragment_5739af76947d76dba90e127f1e8eb825,{},))))))))
  )
}


function Text_9e3a3f911f10a0e97351b6dfd74f7599 () {
  
                useEffect(() => {
                    ((...args) => (addEvents([(ReflexEvent("reflex___state____state.reflex_local_auth___local_auth____local_auth_state.reflex_local_auth___login____login_state.redir", ({  }), ({  })))], args, ({  }))))()
                    return () => {
                        
                    }
                }, []);
const [addEvents, connectErrors] = useContext(EventLoopContext);



  return (
    jsx(RadixThemesText,{as:"p"},"Loading...")
  )
}


function Fragment_adb1ab86bf2761280b78b406339b08df () {
  const reflex___state____state = useContext(StateContexts.reflex___state____state)
const reflex___state____state__reflex_local_auth___local_auth____local_auth_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state)



  return (
    jsx(Fragment,{},((reflex___state____state.is_hydrated_rx_state_ && reflex___state____state__reflex_local_auth___local_auth____local_auth_state.is_authenticated_rx_state_)?(jsx(Fragment_52fae045429d36bc79e4818fbaaf1576,{},)):(jsx(Fragment,{},jsx(RadixThemesFlex,{css:({ ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center" })},jsx(Text_9e3a3f911f10a0e97351b6dfd74f7599,{},))))))
  )
}


export default function Component() {





  return (
    jsx(Fragment,{},jsx(Fragment,{},jsx(Fragment_adb1ab86bf2761280b78b406339b08df,{},)),jsx("title",{},"Uni | Index"),jsx("meta",{content:"favicon.ico",property:"og:image"},))
  )
}