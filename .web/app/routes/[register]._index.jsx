import {Fragment,useCallback,useContext,useEffect,useRef} from "react"
import {Box as RadixThemesBox,Button as RadixThemesButton,Callout as RadixThemesCallout,Card as RadixThemesCard,Flex as RadixThemesFlex,Heading as RadixThemesHeading,Link as RadixThemesLink,Text as RadixThemesText,TextField as RadixThemesTextField} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {ReflexEvent,getRefValue,getRefValues,isTrue,refs} from "$/utils/state"
import {Root as RadixFormRoot} from "@radix-ui/react-form"
import {TriangleAlert as LucideTriangleAlert} from "lucide-react"
import {Link as ReactRouterLink} from "react-router"
import {Helmet} from "react-helmet"
import {jsx} from "@emotion/react"




function Callout__text_ba0750d6b6bbeaf05eced324f6acbad7 () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__reflex_local_auth___registration____registration_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__reflex_local_auth___registration____registration_state)



  return (
    jsx(RadixThemesCallout.Text,{},reflex___state____state__reflex_local_auth___local_auth____local_auth_state__reflex_local_auth___registration____registration_state.error_message_rx_state_)
  )
}


function Fragment_79a7d4367eaf7dbdff86ce5ba61a8727 () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__reflex_local_auth___registration____registration_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__reflex_local_auth___registration____registration_state)



  return (
    jsx(Fragment,{},(!((reflex___state____state__reflex_local_auth___local_auth____local_auth_state__reflex_local_auth___registration____registration_state.error_message_rx_state_?.valueOf?.() === ""?.valueOf?.()))?(jsx(Fragment,{},jsx(RadixThemesCallout.Root,{color:"red",css:({ ["icon"] : "triangle_alert", ["width"] : "100%" }),role:"alert"},jsx(RadixThemesCallout.Icon,{},jsx(LucideTriangleAlert,{},)),jsx(Callout__text_ba0750d6b6bbeaf05eced324f6acbad7,{},)))):(jsx(Fragment,{},))))
  )
}


function Link_49f790220f0e5e47afb37baa3c88f20e () {
  const [addEvents, connectErrors] = useContext(EventLoopContext);

const on_click_bf967679932661b49341445a94d8e17e = useCallback(((_e) => (addEvents([(ReflexEvent("_redirect", ({ ["path"] : "/login", ["external"] : false, ["popup"] : false, ["replace"] : false }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])

  return (
    jsx(RadixThemesLink,{css:({ ["&:hover"] : ({ ["color"] : "var(--accent-8)" }) }),href:"#",onClick:on_click_bf967679932661b49341445a94d8e17e},"Login")
  )
}


function Root_30a08382b63d5235ea93067c79cbf402 () {
  const [addEvents, connectErrors] = useContext(EventLoopContext);
const ref_username = useRef(null); refs["ref_username"] = ref_username;
const ref_password = useRef(null); refs["ref_password"] = ref_password;
const ref_confirm_password = useRef(null); refs["ref_confirm_password"] = ref_confirm_password;

    const handleSubmit_f6d94934f415a546459f15b81a8fbd1e = useCallback((ev) => {
        const $form = ev.target
        ev.preventDefault()
        const form_data = {...Object.fromEntries(new FormData($form).entries()), ...({ ["username"] : getRefValue(refs["ref_username"]), ["password"] : getRefValue(refs["ref_password"]), ["confirm_password"] : getRefValue(refs["ref_confirm_password"]) })};

        (((...args) => (addEvents([(ReflexEvent("reflex___state____state.reflex_local_auth___local_auth____local_auth_state.reflex_local_auth___registration____registration_state.handle_registration", ({ ["form_data"] : form_data }), ({  })))], args, ({  }))))(ev));

        if (false) {
            $form.reset()
        }
    })
    


  return (
    jsx(RadixFormRoot,{className:"Root ",css:({ ["width"] : "100%" }),onSubmit:handleSubmit_f6d94934f415a546459f15b81a8fbd1e},jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["minWidth"] : "50vw" }),direction:"column",gap:"3"},jsx(RadixThemesHeading,{size:"7"},"Create an account"),jsx(Fragment_79a7d4367eaf7dbdff86ce5ba61a8727,{},),jsx(RadixThemesText,{as:"p"},"Username"),jsx(RadixThemesTextField.Root,{css:({ ["width"] : "100%" }),id:"username",name:"username",placeholder:"Username",ref:ref_username},),jsx(RadixThemesText,{as:"p"},"Password"),jsx(RadixThemesTextField.Root,{css:({ ["width"] : "100%" }),id:"password",name:"password",placeholder:"Password",ref:ref_password,type:"password"},),jsx(RadixThemesText,{as:"p"},"Confirm Password"),jsx(RadixThemesTextField.Root,{css:({ ["width"] : "100%" }),id:"confirm_password",name:"confirm_password",placeholder:"Confirm Password",ref:ref_confirm_password,type:"password"},),jsx(RadixThemesButton,{css:({ ["width"] : "100%" })},"Sign up"),jsx(RadixThemesFlex,{css:({ ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center", ["width"] : "100%" })},jsx(Link_49f790220f0e5e47afb37baa3c88f20e,{},))))
  )
}


function Fragment_832d612542c7c8c1286a5ca6c602fb94 () {
  const reflex___state____state__reflex_local_auth___local_auth____local_auth_state__reflex_local_auth___registration____registration_state = useContext(StateContexts.reflex___state____state__reflex_local_auth___local_auth____local_auth_state__reflex_local_auth___registration____registration_state)



  return (
    jsx(Fragment,{},(reflex___state____state__reflex_local_auth___local_auth____local_auth_state__reflex_local_auth___registration____registration_state.success_rx_state_?(jsx(Fragment,{},jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",direction:"column",gap:"3"},jsx(RadixThemesText,{as:"p"},"Registration successful!")))):(jsx(Fragment,{},jsx(RadixThemesCard,{},jsx(Root_30a08382b63d5235ea93067c79cbf402,{},))))))
  )
}


export default function Component() {





  return (
    jsx(Fragment,{},jsx(RadixThemesBox,{css:({ ["width"] : "100vw", ["height"] : "100vh", ["position"] : "relative", ["overflow"] : "hidden" })},jsx("img",{css:({ ["position"] : "fixed", ["top"] : "0", ["left"] : "0", ["width"] : "100vw", ["height"] : "100vh", ["objectFit"] : "cover", ["zIndex"] : "-1" }),src:"/bg_image.png"},),jsx(RadixThemesFlex,{css:({ ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center", ["height"] : "100vh", ["zIndex"] : "1" })},jsx(RadixThemesFlex,{css:({ ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center", ["paddingTop"] : "10vh" })},jsx(Fragment_832d612542c7c8c1286a5ca6c602fb94,{},))),jsx(Helmet,{},jsx("script",{},"(function(){function a(){return'<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"20\" height=\"20\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"#00ff88\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z\"/><circle cx=\"12\" cy=\"12\" r=\"3\"/></svg>';}function b(){return'<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"20\" height=\"20\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"#00ff88\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24\"/><line x1=\"1\" y1=\"1\" x2=\"23\" y2=\"23\"/></svg>';}function c(){try{if(!document.body)return;document.querySelectorAll('input[type=\"password\"]:not([data-eye-attached])').forEach(function(inp){try{inp.setAttribute('data-eye-attached','1');var w=document.createElement('div');w.style.cssText='position:relative;display:block;width:100%;';inp.parentNode.insertBefore(w,inp);w.appendChild(inp);var btn=document.createElement('button');btn.type='button';btn.style.cssText='position:absolute;right:10px;top:50%;transform:translateY(-50%);background:none;border:none;padding:0;cursor:pointer;color:#00ff88;z-index:99999;display:flex;align-items:center;';btn.innerHTML=a();btn.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();inp.type=inp.type==='password'?(btn.innerHTML=b(),'text'):(btn.innerHTML=a(),'password');});w.appendChild(btn);inp.style.paddingRight='40px';}catch(e){}});}catch(e){}}c();var t=0,iv=setInterval(function(){c();if(++t>60)clearInterval(iv);},300);try{new MutationObserver(c).observe(document.body,{childList:true,subtree:true});}catch(e){}})();"))),jsx("title",{},"Register"),jsx("meta",{content:"favicon.ico",property:"og:image"},))
  )
}