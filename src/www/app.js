function poblarUsuarios(){
  var empezando=True
  $.get("/personal").then(function(personal){
    if (personal.length) $("#usuarios").empty();
    personal.forEach(function(p){
      $("#usuarios").append(`
        <div class="col s12 m4">
          <div class="icon-block center-align" id="usuario_${p.id}">
            <img id="rostro_${p.id}" src="/personal/${p.id}/rostros"/>
            <a id="del_${p.id}" class="btn-floating waves-effect waves-light red"><i class="material-icons">delete</i></a>
            <h5 class="center">${p.nombre}</h5>
            <p class="light center">${p.habilitado?'Habilitado':'Bloqueado'}</p>
            <a class="btn" id="reg_${p.id}">Tomar Foto</a>
            
          </div>
        </div>
      `); //<a class="btn" id="reg_${p.id}">Borrar Fotos</a>
      if (empezando){
        $(`#del_${p.id}`).remove();
      } else {
        $(`#del_${p.id}`).off('click').click(function(){
          $.ajax({
            url: `/personal/${p.id}`,
            type: 'DELETE',
            success: function(result) {
                // Do something with the result
                poblarUsuarios(); //reload
            }
          });
        });        
      }
      $(`#reg_${p.id}`).off('click').click(function(){
        //estará ocupado?
        //mostrar modal stream!
        $("#stream").append(` <img id="bg" src="/video_feed" width="320px">`)
        $("#modalStream").modal('open');
        $.post(`/personal/${p.id}/rostros`).then(function(data){
          $("#stream").empty();
          $("#modalStream").modal('close');
          console.log(data)
          Materialize.toast('Rostro Registrado Correctamente!', 4000)
          $(`#rostro_${p.id}`).attr('src',`/personal/${p.id}/rostros?id=${data.id}`)
        }).catch(function(data){
          $("#stream").empty();
          $("#modalStream").modal('close');
          console.error("Error",data)
          Materialize.toast('No se encotró un Rostro válido', 4000)
        })
      });
      $(`#rostro_${p.id}`).off('click').click(function(){
        $("#uNombre").text(p.nombre);
        $("#uRostros").text("Rostros registrados: "+p.rostros);
        $("#uHabilitado").off("click");
        $('#uHabilitado').prop('checked',p.habilitado);
        $("#uHabilitado").click(function(){
          var nuevo =$("#uHabilitado").is(':checked')?1:0;
          $.ajax({
            url: `/personal/${p.id}`,
            type: 'PUT',
            data: {habilitado:nuevo},
            success: function(result) {
                // Do something with the result
                //$(`#rostro_${p.id}`).click(); //reload
            }
          });
        })
        $("#uRostrosArray").empty();
        $.get(`/personal/${p.id}/rostros?index=-1`).then(function(datos){
          if(!datos) return;
          Object.keys(datos).forEach(function(r_id){
            $("#uRostrosArray").append(`
              <img id="r_${r_id}" src="${datos[r_id]}"/>
            `);
            $(`#r_${r_id}`).off('click').click(function(){
              //borrar este rostro?
              $.ajax({
                url: `/personal/${p.id}/rostros?id=${r_id}`,
                type: 'DELETE',
                success: function(result) {
                    // Do something with the result
                    $(`#rostro_${p.id}`).click(); //reload
                }
              });
            });
          });
        });
        $("#modalUsuario").modal('open');
      });
    });
  });
}
/*
function confirm(text){
  $("#confirmText").text(text);
  $("#confirmModal").modal('open');

}*/


jQuery(function($){ //dom ready
  moment.locale('es');
  Highcharts.setOptions({
    global: {
      useUTC: false
    }
  });
  $("#modalCrear").modal({});
  $("#modalUsuario").modal({});
  $("#modalStream").modal({dismissible: false,});
  $(".button-collapse").sideNav();
  poblarUsuarios();
  $(".btnCrear").click(function(){
    //abrir modal
    $("#modalCrear").modal('open');
    $("#btnCrearNuevo").off('click').click(function(){
      console.log("iniciando registro")
      $.post("/personal",{
        usuario : $("#usuario").val(),
        tipo: 1
      },function(data){
        $("#modalCrear").modal('close');
        Materialize.toast('Usuario Creado', 4000)
        poblarUsuarios();
      });
    });
  });


  $(".btnBuscar").click(function(){
    $("#stream").append(` <img id="bg" src="/video_feed" width="320px">`)
    $("#modalStream").modal('open');    
    $.get("/buscar").then(function(data){
      $("#stream").empty();
      $("#modalStream").modal('close');
      console.log("Error",data)
      Materialize.toast(`Usuario ${data.usuario.nombre} Identificado!`, 4000)
    }).catch(function(data){
      $("#stream").empty();
      $("#modalStream").modal('close');
      console.error("Error",data)
      Materialize.toast('No se encotró un Rostro válido', 4000)
    })
  });

  $.get("/brillo").then(function(valor){
    $("#brillo").val(valor);
    $("#brillo").change(function(){
      $.post("/brillo",{valor:$("#brillo").val()}).then(function(data){
        console.log('brillo',data);
      })
    })
  });
  $.get("/contraste").then(function(valor){
    $("#contraste").val(valor);
    $("#contraste").change(function(){
      $.post("/contraste",{valor:$("#contraste").val()}).then(function(data){
        console.log('contraste',data);
      })
    })
  });
    

  setInterval(function(){
    $("#hora").text(moment().format('LLLL:ss'));
  },1000);
});