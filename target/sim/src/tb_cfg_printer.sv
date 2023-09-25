module tb_cfg_printer #(
  /// The selected simulation configuration from the `tb_cheshire_pkg`.
  parameter int unsigned SelectedCfg = 32'd0
);
  import cheshire_pkg::*;
  import tb_cheshire_pkg::*;
  localparam cheshire_cfg_t DutCfg = TbCheshireConfigs[SelectedCfg];
  // import "DPI-C" function void format_cfg(input string cfg_str, input int length);
  //
  // initial begin
  //   static string cfg_str = $sformatf("%p", DutCfg);
  //   format_cfg(cfg_str, cfg_str.len());
  // end


  initial begin
    // constants
    static int unsigned int_hex_split    = 4096;
    static int unsigned param_name_width = 24;

    // get the string
    static string cfg_str  = $sformatf("%p", DutCfg);
    static integer cfg_len = cfg_str.len();

    // temp variables
    static string       cfg_item      = "";
    static bit          array_active  = 0;
    static bit          unnamed_array = 0;
    static bit          was_closed    = 0;
    static int unsigned unnamed_idx   = 0;

    // terminate config string
    cfg_str.putc(cfg_len-1, ",");

    // parse each character individually
    for (int i = 2; i < cfg_len; i++) begin

      // colon
      if (cfg_str[i] == ":") begin
        // we print a key
        automatic string padding = "";

        // decide if we are in array mode
        if (array_active) begin
          for (int p = 0; p < param_name_width - cfg_item.len() - 4; p++) begin
            padding = {padding, " "};
          end
          $write("    %s:%s", cfg_item, padding);
        end else begin
          for (int p = 0; p < param_name_width - cfg_item.len(); p++) begin
            padding = {padding, " "};
          end
          $write("%s:%s", cfg_item, padding);
        end
        cfg_item = "";

        // differentiate between unnamed and named arrays
        if (array_active) begin
          unnamed_array = 0;
        end

      // comma
      end else if (cfg_str[i] == ",") begin
        automatic longint unsigned value = cfg_item.atoi();
        automatic string unnamed_idx_str = $sformatf("%-0d", unnamed_idx);
        automatic string padding         = "";

        // we print the unnamed array index
        if (array_active & unnamed_array) begin
          for (int p = 0; p < param_name_width - unnamed_idx_str.len() - 4; p++) begin
            padding = {padding, " "};
          end
          $write("    %s:%s", unnamed_idx_str, padding);
        end

        // we print a value
        if (value < int_hex_split) begin
          $write(" %d", value);
        end else begin
          automatic string hex_val = $sformatf("%h", value);
          $write("0x");
          for (int h = 0; h < hex_val.len(); h++) begin
            if (h % 4 == 0 && h > 0) begin
              $write("_");
            end
            $write("%s", hex_val[h]);
          end
        end
        cfg_item = "";

        // array bookkeeping
        unnamed_idx = unnamed_idx + 1;
        if (was_closed) begin
          was_closed   = 0;
          array_active = 0;
        end

        // finish entry
        $write("\n");

      // space: ignore
      end else if (cfg_str[i] == " ") begin
        continue;

      // ': ignore
      end else if (cfg_str[i] == "'") begin
        continue;

      // }: ignore
      end else if (cfg_str[i] == "}") begin
        was_closed = 1;

      // {: begin array
      end else if (cfg_str[i] == "{") begin
        array_active  = 1;
        unnamed_array = 1;
        unnamed_idx   = 0;
        $write("\n");

      // append key or value
      end else begin
        cfg_item = {cfg_item, cfg_str[i]};
      end
    end
  end

endmodule
