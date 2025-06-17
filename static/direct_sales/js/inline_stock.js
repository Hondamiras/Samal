// static/direct_sales/js/inline_stock.js

(function($) {
    $(function(){
      function updateStock($sel) {
        // достаём остаток, или 0
        var stock = parseInt($sel.find('option:selected').data('stock')) || 0;
        var $row  = $sel.closest('tr');
  
        // обновляем колонку «В наличии»
        $row.find('td.field-available_stock').text(stock);
  
        // находим input quantity и пишем ему min/max
        var $qty = $row.find('input[name$="-quantity"]');
        $qty.attr('min', 1);
        $qty.attr('max', stock);
      }
  
      // инициализация при загрузке страницы
      $('select[name$="-product_variant"]').each(function(){
        updateStock($(this));
      });
  
      // обновление при смене селекта
      $(document).on('change', 'select[name$="-product_variant"]', function(){
        updateStock($(this));
      });
    });
  })(django.jQuery);
  
