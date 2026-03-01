import {Fragment,useCallback,useContext,useEffect,useRef} from "react"
import {Box as RadixThemesBox,Button as RadixThemesButton,Callout as RadixThemesCallout,Card as RadixThemesCard,Flex as RadixThemesFlex,Heading as RadixThemesHeading,Link as RadixThemesLink,Text as RadixThemesText,TextField as RadixThemesTextField} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {ReflexEvent,getRefValue,getRefValues,isTrue,refs} from "$/utils/state"
import {Root as RadixFormRoot} from "@radix-ui/react-form"
import {TriangleAlert as LucideTriangleAlert} from "lucide-react"
import {Link as ReactRouterLink} from "react-router"
import {Helmet} from "react-helmet"
import {jsx} from "@emotion/react"




function Callout__text_8c0d04114be123a192b2a6586af8a274 () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__reflex_local_auth___login____login_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__reflex_local_auth___login____login_state)



  return (
    jsx(RadixThemesCallout.Text,{},reflex___state____state__reflex_local_auth___local_auth____local_auth_state__reflex_local_auth___login____login_state.error_message_rx_state_)
  )
}


function Fragment_95a81264743b864f5f209877b5ec1889 () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__reflex_local_auth___login____login_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__reflex_local_auth___login____login_state)



  return (
    jsx(Fragment,{},(!((reflex___state____state__reflex_local_auth___local_auth____local_auth_state__reflex_local_auth___login____login_state.error_message_rx_state_?.valueOf?.() === ""?.valueOf?.()))?(jsx(Fragment,{},jsx(RadixThemesCallout.Root,{color:"red",css:({ ["icon"] : "triangle_alert", ["width"] : "100%" }),role:"alert"},jsx(RadixThemesCallout.Icon,{},jsx(LucideTriangleAlert,{},)),jsx(Callout__text_8c0d04114be123a192b2a6586af8a274,{},)))):(jsx(Fragment,{},))))
  )
}


function Link_456074f5b6b8a0a8d7793896f5a9c0f5 () {
  const [addEvents, connectErrors] = useContext(EventLoopContext);

const on_click_b2a4273178446bea7dbdba710a5e6dd8 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.reflex_local_auth___local_auth____local_auth_state.reflex_local_auth___registration____registration_state.redir", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])

  return (
    jsx(RadixThemesLink,{css:({ ["&:hover"] : ({ ["color"] : "var(--accent-8)" }) }),href:"#",onClick:on_click_b2a4273178446bea7dbdba710a5e6dd8},"Register")
  )
}


function Root_5ff28c46cb7bb60cfcb4fb6133e0a9cd () {
  const [addEvents, connectErrors] = useContext(EventLoopContext);
const ref_username = useRef(null); refs["ref_username"] = ref_username;
const ref_password = useRef(null); refs["ref_password"] = ref_password;

    const handleSubmit_ad0a32e0f030db62a1de3ecd5136fec1 = useCallback((ev) => {
        const $form = ev.target
        ev.preventDefault()
        const form_data = {...Object.fromEntries(new FormData($form).entries()), ...({ ["username"] : getRefValue(refs["ref_username"]), ["password"] : getRefValue(refs["ref_password"]) })};

        (((...args) => (addEvents([(ReflexEvent("reflex___state____state.reflex_local_auth___local_auth____local_auth_state.reflex_local_auth___login____login_state.on_submit", ({ ["form_data"] : form_data }), ({  })))], args, ({  }))))(ev));

        if (false) {
            $form.reset()
        }
    })
    


  return (
    jsx(RadixFormRoot,{className:"Root ",css:({ ["width"] : "100%" }),onSubmit:handleSubmit_ad0a32e0f030db62a1de3ecd5136fec1},jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["minWidth"] : "50vw" }),direction:"column",gap:"3"},jsx(RadixThemesHeading,{size:"7"},"Login into your Account"),jsx(Fragment_95a81264743b864f5f209877b5ec1889,{},),jsx(RadixThemesText,{as:"p"},"Username"),jsx(RadixThemesTextField.Root,{css:({ ["width"] : "100%" }),id:"username",name:"username",placeholder:"Username",ref:ref_username},),jsx(RadixThemesText,{as:"p"},"Password"),jsx(RadixThemesTextField.Root,{css:({ ["width"] : "100%" }),id:"password",name:"password",placeholder:"Password",ref:ref_password,type:"password"},),jsx(RadixThemesButton,{css:({ ["width"] : "100%" })},"Sign in"),jsx(RadixThemesFlex,{css:({ ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center", ["width"] : "100%" })},jsx(Link_456074f5b6b8a0a8d7793896f5a9c0f5,{},))))
  )
}


function Fragment_765c26ebfd9f08f8a10f5ff87eb425f0 () {
  const reflex___state____state = useContext(StateContexts.reflex___state____state)



  return (
    jsx(Fragment,{},(reflex___state____state.is_hydrated_rx_state_?(jsx(Fragment,{},jsx(RadixThemesCard,{},jsx(Root_5ff28c46cb7bb60cfcb4fb6133e0a9cd,{},)))):(jsx(Fragment,{},))))
  )
}


export default function Component() {





  return (
    jsx(Fragment,{},jsx(RadixThemesBox,{css:({ ["width"] : "100vw", ["height"] : "100vh", ["position"] : "relative", ["overflow"] : "hidden" })},jsx("img",{css:({ ["position"] : "fixed", ["top"] : "0", ["left"] : "0", ["width"] : "100vw", ["height"] : "100vh", ["objectFit"] : "cover", ["zIndex"] : "-1" }),src:"/bg_image.png"},),jsx(RadixThemesFlex,{css:({ ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center", ["height"] : "100vh", ["zIndex"] : "1" })},jsx(RadixThemesFlex,{css:({ ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center", ["paddingTop"] : "10vh" })},jsx(Fragment_765c26ebfd9f08f8a10f5ff87eb425f0,{},))),jsx(Helmet,{},jsx("script",{},"(function(){function a(){return'<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"20\" height=\"20\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"#00ff88\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z\"/><circle cx=\"12\" cy=\"12\" r=\"3\"/></svg>';}function b(){return'<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"20\" height=\"20\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"#00ff88\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24\"/><line x1=\"1\" y1=\"1\" x2=\"23\" y2=\"23\"/></svg>';}function c(){try{if(!document.body)return;document.querySelectorAll('input[type=\"password\"]:not([data-eye-attached])').forEach(function(inp){try{inp.setAttribute('data-eye-attached','1');var w=document.createElement('div');w.style.cssText='position:relative;display:block;width:100%;';inp.parentNode.insertBefore(w,inp);w.appendChild(inp);var btn=document.createElement('button');btn.type='button';btn.style.cssText='position:absolute;right:10px;top:50%;transform:translateY(-50%);background:none;border:none;padding:0;cursor:pointer;color:#00ff88;z-index:99999;display:flex;align-items:center;';btn.innerHTML=a();btn.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();inp.type=inp.type==='password'?(btn.innerHTML=b(),'text'):(btn.innerHTML=a(),'password');});w.appendChild(btn);inp.style.paddingRight='40px';}catch(e){}});}catch(e){}}c();var t=0,iv=setInterval(function(){c();if(++t>60)clearInterval(iv);},300);try{new MutationObserver(c).observe(document.body,{childList:true,subtree:true});}catch(e){}})();"))),jsx("title",{},"Login"),jsx("meta",{content:"favicon.ico",property:"og:image"},))
  )
}